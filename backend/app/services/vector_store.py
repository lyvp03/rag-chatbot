"""ChromaDB vector store service for document storage and similarity search.

"""

import uuid
import logging
from typing import Any

import chromadb
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document

from app.config import settings

logger = logging.getLogger(__name__)


class VectorStoreService:
    """Manages ChromaDB operations: add, search, delete, and stats.
    """

    def __init__(self):
        # ── Embedding model  ──────────────
        self._embedding_model = OpenAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            api_key=settings.EMBEDDING_API_KEY,
            base_url=settings.EMBEDDING_API_URL,
        )

        # ── ChromaDB persistent client ───────────────────────────────────

        chroma_dir = str(settings.chroma_path)

        self._client = chromadb.PersistentClient(path=chroma_dir)

        # ── LangChain Chroma wrapper ─────────────────────────────────────
        self._store = Chroma(
            client=self._client,
            collection_name="rag_documents",
            embedding_function=self._embedding_model,
        )

        logger.info(
            f"VectorStoreService initialized with ChromaDB. Path: {chroma_dir}"
        )

    # -----------------------------------------------------------------------
    # Retriever interface 
    # -----------------------------------------------------------------------

    @property
    def retriever(self):
        """Get a LangChain retriever interface for the vector store."""
        return self._store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 5},
        )

    # -----------------------------------------------------------------------
    # Add
    # -----------------------------------------------------------------------

    async def add_documents(self, documents: list[Document]) -> list[str]:
        """Add chunked documents to the ChromaDB collection.

        ChromaDB auto-persists — no save_local() needed.
        """
        if not documents:
            return []

        ids = [str(uuid.uuid4()) for _ in documents]

        logger.info(f"Adding {len(documents)} chunks to ChromaDB store")
        self._store.add_documents(documents, ids=ids)
        logger.info(f"Successfully added {len(ids)} chunks")

        return ids

    # -----------------------------------------------------------------------
    # Search
    # -----------------------------------------------------------------------

    async def similarity_search(
        self, query: str, k: int = 5
    ) -> list[tuple[Document, float]]:
        """Semantic similarity search.

        No system-doc filtering needed (ChromaDB has no init dummy doc).
        """
        results = self._store.similarity_search_with_relevance_scores(query, k=k)
        logger.info(
            f"Search for '{query[:50]}...' returned {len(results)} results"
        )
        return results

    # -----------------------------------------------------------------------
    # Delete
    # -----------------------------------------------------------------------

    async def delete_by_doc_id(self, doc_id: str) -> int:
        """Delete all chunks belonging to a document.

        ChromaDB supports native metadata filtering.
        """
        try:
            # Get all chunk IDs that belong to this document
            result = self._store._collection.get(
                where={"doc_id": doc_id}
            )
            ids_to_delete = result.get("ids", [])

            if ids_to_delete:
                self._store.delete(ids=ids_to_delete)
                logger.info(
                    f"Deleted {len(ids_to_delete)} chunks for doc_id={doc_id}"
                )

            return len(ids_to_delete)

        except Exception as e:
            logger.error(f"Error deleting doc_id={doc_id}: {e}")
            return 0

    # -----------------------------------------------------------------------
    # Stats & Metadata
    # -----------------------------------------------------------------------

    async def get_collection_stats(self) -> dict[str, Any]:
        """Get statistics about the current ChromaDB collection."""
        try:
            count = self._store._collection.count()
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            count = 0

        return {
            "collection_name": "rag_documents",
            "total_chunks": count,
        }

    async def get_documents_metadata(self) -> list[dict[str, Any]]:
        """Get metadata for all unique documents in the store.

        ChromaDB returns metadata directly.
        """
        try:
            result = self._store._collection.get(include=["metadatas"])
            metadatas = result.get("metadatas") or []

            docs_map: dict[str, dict[str, Any]] = {}
            for metadata in metadatas:
                if not metadata:
                    continue

                doc_id = metadata.get("doc_id", "unknown")
                if doc_id not in docs_map:
                    docs_map[doc_id] = {
                        "doc_id":      doc_id,
                        "filename":    metadata.get("filename",    "unknown"),
                        "file_type":   metadata.get("file_type",   "unknown"),
                        "uploaded_at": metadata.get("uploaded_at", ""),
                        "chunk_count": 0,
                    }
                docs_map[doc_id]["chunk_count"] += 1

            return list(docs_map.values())

        except Exception as e:
            logger.error(f"Error getting documents metadata: {e}")
            return []
