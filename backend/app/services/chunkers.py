"""
Chunking strategies for the RAG pipeline.

Strategy matrix
---------------
.txt    → Semantic  (chonkie SemanticChunker)  [fallback: fixed]
.md     → Structured (MarkdownHeaderTextSplitter) [fallback: fixed]
.pdf    → Fixed     (RecursiveCharacterTextSplitter)
audio   → Fixed     (RecursiveCharacterTextSplitter, chunk_type="audio")
"""

import logging
from langchain_core.documents import Document
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    MarkdownHeaderTextSplitter,
)
from chonkie import SemanticChunker

from app.config import settings
from app.services.audio_processor import SUPPORTED_AUDIO_EXTENSIONS
from app.services.loaders import SEMANTIC_EXTENSIONS, STRUCTURED_EXTENSIONS

logger = logging.getLogger(__name__)

MARKDOWN_HEADERS = [
    ("#",   "H1"),
    ("##",  "H2"),
    ("###", "H3"),
]


class DocumentChunker:
    """Chunks raw Documents using the appropriate strategy for each file type."""

    def __init__(self):
        # Semantic chunker – for .txt
        self.semantic_chunker = SemanticChunker(
            embedding_model="minishlab/potion-base-8M",
            threshold=0.7,
            chunk_size=512,
        )

        # Fixed chunker – fallback / PDF / audio
        self.fixed_chunker = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

        # Structured splitter – for .md
        self.markdown_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=MARKDOWN_HEADERS,
            strip_headers=False,
        )

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    def chunk(self, raw_documents: list[Document], suffix: str) -> list[Document]:
        """
        Dispatch to the correct chunking strategy based on file extension.

        Returns a flat list of chunked Documents with chunk_type and section
        metadata already set.
        """
        if suffix in STRUCTURED_EXTENSIONS:
            logger.info(f"Strategy: structured  ({suffix})")
            return self._chunk_structured(raw_documents)

        if suffix in SEMANTIC_EXTENSIONS:
            logger.info(f"Strategy: semantic  ({suffix})")
            return self._chunk_semantic(raw_documents)

        logger.info(f"Strategy: fixed  ({suffix})")
        return self._chunk_fixed(raw_documents, suffix)

    # -----------------------------------------------------------------------
    # Strategy implementations
    # -----------------------------------------------------------------------

    def _chunk_structured(self, raw_documents: list[Document]) -> list[Document]:
        """
        Split Markdown by headers (H1/H2/H3), then sub-chunk sections that
        exceed settings.CHUNK_SIZE with the fixed splitter.

        Metadata added: section (header value), chunk_type="structured"
        """
        full_text = "\n\n".join(doc.page_content for doc in raw_documents)

        try:
            header_chunks = self.markdown_splitter.split_text(full_text)
        except Exception as e:
            logger.warning(f"Structured chunking failed: {e} – falling back to fixed")
            return self._apply_fixed_metadata(
                self.fixed_chunker.split_documents(raw_documents),
                chunk_type="fixed",
            )

        chunks: list[Document] = []
        for hc in header_chunks:
            section = (
                hc.metadata.get("H3")
                or hc.metadata.get("H2")
                or hc.metadata.get("H1")
                or "Unknown"
            )
            if len(hc.page_content) > settings.CHUNK_SIZE:
                for sub in self.fixed_chunker.split_documents([hc]):
                    sub.metadata["section"]    = section
                    sub.metadata["chunk_type"] = "structured"
                    chunks.append(sub)
            else:
                hc.metadata["section"]    = section
                hc.metadata["chunk_type"] = "structured"
                chunks.append(hc)

        return [c for c in chunks if c.page_content.strip()]

    def _chunk_semantic(self, raw_documents: list[Document]) -> list[Document]:
        """
        Chunk using chonkie SemanticChunker.
        Falls back to fixed chunking on error.

        Metadata added: section="Unknown", chunk_type="semantic"
        """
        full_text = "\n\n".join(doc.page_content for doc in raw_documents)

        try:
            return [
                Document(
                    page_content=chunk.text,
                    metadata={"section": "Unknown", "chunk_type": "semantic"},
                )
                for chunk in self.semantic_chunker.chunk(full_text)
                if chunk.text.strip()
            ]
        except Exception as e:
            logger.warning(f"Semantic chunking failed: {e} – falling back to fixed")
            return self._apply_fixed_metadata(
                self.fixed_chunker.split_documents(raw_documents),
                chunk_type="fixed",
            )

    def _chunk_fixed(self, raw_documents: list[Document], suffix: str) -> list[Document]:
        """
        RecursiveCharacterTextSplitter for PDF, audio, and other file types.
        Table Documents (chunk_type="table") from pdfplumber are preserved as-is.

        Metadata added: chunk_type="audio" | "fixed", section (preserved or "Unknown")
        """
        chunk_type = "audio" if suffix in SUPPORTED_AUDIO_EXTENSIONS else "fixed"

        table_docs = [d for d in raw_documents if d.metadata.get("chunk_type") == "table"]
        text_docs  = [d for d in raw_documents if d.metadata.get("chunk_type") != "table"]

        split_docs = self._apply_fixed_metadata(
            self.fixed_chunker.split_documents(text_docs),
            chunk_type=chunk_type,
        )

        return split_docs + table_docs

    # -----------------------------------------------------------------------
    # Helper
    # -----------------------------------------------------------------------

    @staticmethod
    def _apply_fixed_metadata(
        docs: list[Document], chunk_type: str
    ) -> list[Document]:
        """Ensure section and chunk_type metadata are set on every document."""
        for doc in docs:
            doc.metadata.setdefault("section",    doc.metadata.get("section", "Unknown"))
            doc.metadata.setdefault("chunk_type", chunk_type)
        return docs
