"""FAISS vector store service for document storage and similarity search."""
import os
import uuid
import logging
from typing import Any
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from app.config import settings

logger = logging.getLogger(__name__)

class VectorStoreService:
    """Manages FAISS operations: add, search, delete, and stats."""

    def __init__(self):
        self._embedding_model = OpenAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            api_key=settings.EMBEDDING_API_KEY,       
            base_url=settings.EMBEDDING_API_URL,        
        )
        self._faiss_dir = settings.faiss_path
        self._faiss_index_name = "index"
        logger.info(f"VectorStoreService initialized with FAISS. Path: {self._faiss_dir}")
        self._ensure_index()

    def _ensure_index(self):
        """Creates an empty FAISS index if it doesn't exist."""
        if not self._faiss_dir.exists() or not (self._faiss_dir / f"{self._faiss_index_name}.faiss").exists():
            logger.info("Creating new FAISS index...")
            doc = Document(page_content="System initialization", metadata={"system": True, "doc_id": "system_init"})
            vector_store = FAISS.from_documents([doc], self._embedding_model)
            vector_store.save_local(str(self._faiss_dir), self._faiss_index_name)

    def _load_store(self) -> FAISS:
        """Loads FAISS vector store from disk."""
        return FAISS.load_local(
            str(self._faiss_dir),
            self._embedding_model,
            index_name=self._faiss_index_name,
            allow_dangerous_deserialization=True
        )

    @property
    def retriever(self):
        """Get a retriever interface for the vector store."""
        store = self._load_store()
        return store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": 5},
        )

    async def add_documents(self, documents: list[Document]) -> list[str]:
        if not documents:
            return []
        logger.info(f"Adding {len(documents)} chunks to FAISS store")
        ids = [str(uuid.uuid4()) for _ in documents]
        store = self._load_store()
        store.add_documents(documents, ids=ids)
        store.save_local(str(self._faiss_dir), self._faiss_index_name)
        logger.info(f"Successfully added {len(ids)} chunks")
        return ids

    async def similarity_search(
        self, query: str, k: int = 5
    ) -> list[tuple[Document, float]]:
        store = self._load_store()
        results = store.similarity_search_with_relevance_scores(query, k=k)
        filtered_results = [r for r in results if r[0].metadata.get("system") is not True]
        logger.info(f"Search for '{query[:50]}...' returned {len(filtered_results)} results")
        return filtered_results

    async def delete_by_doc_id(self, doc_id: str) -> int:
        store = self._load_store()
        doc_ids_to_delete = []
        for p_id, doc in store.docstore._dict.items():
            if doc.metadata.get("doc_id") == doc_id:
                doc_ids_to_delete.append(p_id)
        if doc_ids_to_delete:
            store.delete(doc_ids_to_delete)
            store.save_local(str(self._faiss_dir), self._faiss_index_name)
            logger.info(f"Deleted {len(doc_ids_to_delete)} chunks for doc_id={doc_id}")
        return len(doc_ids_to_delete)

    async def get_collection_stats(self) -> dict[str, Any]:
        """Get statistics about the current collection."""
        try:
            store = self._load_store()
            count = len([d for d in store.docstore._dict.values() if d.metadata.get("system") is not True])
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            count = 0
        return {
            "collection_name": "faiss_index",   
            "total_chunks": count,
        }

    async def get_documents_metadata(self) -> list[dict[str, Any]]:
        """Get metadata for all unique documents in the store."""
        try:
            store = self._load_store()
            docs_map: dict[str, dict[str, Any]] = {}
            for doc in store.docstore._dict.values():
                metadata = doc.metadata
                if metadata.get("system") is True:
                    continue
                doc_id = metadata.get("doc_id", "unknown")
                if doc_id not in docs_map:
                    docs_map[doc_id] = {
                        "doc_id": doc_id,
                        "filename": metadata.get("filename", "unknown"),
                        "file_type": metadata.get("file_type", "unknown"),
                        "uploaded_at": metadata.get("uploaded_at", ""),
                        "chunk_count": 0,
                    }
                docs_map[doc_id]["chunk_count"] += 1
            return list(docs_map.values())
        except Exception as e:
            logger.error(f"Error getting documents metadata: {e}")
            return []