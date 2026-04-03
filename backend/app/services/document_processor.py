"""

Orchestrator: loads a file, chunks it, and enriches chunk metadata.

Pipeline
--------
    DocumentLoader  →  raw Documents
    DocumentChunker →  chunked Documents
    metadata loop   →  enriched Documents  (ready for vectorization)
"""

import logging
from pathlib import Path
from datetime import datetime, timezone

from langchain_core.documents import Document

from app.services.loaders import DocumentLoader
from app.services.chunkers import DocumentChunker

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """
    Thin orchestrator that wires together DocumentLoader and DocumentChunker.

    Usage
    -----
        processor = DocumentProcessor()
        chunks    = await processor.process_file(Path("report.pdf"), doc_id="abc123")
    """

    def __init__(self):
        self.loader  = DocumentLoader()
        self.chunker = DocumentChunker()

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    async def process_file(self, file_path: Path, doc_id: str) -> list[Document]:
        """
        Full pipeline: load → chunk → enrich metadata.

        Args:
            file_path : Path to the uploaded file.
            doc_id    : Unique document identifier for metadata tracking.

        Returns:
            List of chunked Documents with enriched metadata, ready for embedding.
        """
        suffix    = file_path.suffix.lower()
        filename  = file_path.name
        timestamp = datetime.now(timezone.utc).isoformat()

        logger.info(f"Processing: {filename}")

        # Step 1 – Load
        raw_documents = await self.loader.load(file_path)
        if not raw_documents:
            logger.warning(f"No content extracted from {filename}")
            return []

        # Step 2 – Chunk
        chunks = self.chunker.chunk(raw_documents, suffix)
        if not chunks:
            logger.warning(f"No chunks created from {filename}")
            return []

        # Step 3 – Enrich metadata
        for i, chunk in enumerate(chunks):
            chunk.metadata.update({
                "doc_id":             doc_id,
                "filename":           filename,
                "file_type":          suffix.lstrip("."),
                "chunk_index":        i,
                "total_chunks":       len(chunks),
                "uploaded_at":        timestamp,
                "chunk_type":         chunk.metadata.get("chunk_type",  "fixed"),
                "section":            chunk.metadata.get("section",     "Unknown"),
                # legacy field kept for backwards-compat
                "chunking_strategy":  chunk.metadata.get("chunk_type",  "fixed"),
            })

        logger.info(
            f"Done: {filename} → {len(chunks)} chunks "
            f"(strategy: {chunks[0].metadata.get('chunking_strategy')})"
        )
        return chunks

    # -----------------------------------------------------------------------
    # Convenience delegators
    # -----------------------------------------------------------------------

    def is_supported(self, filename: str) -> bool:
        """Delegate to DocumentLoader.is_supported."""
        return self.loader.is_supported(filename)

    def get_supported_extensions(self) -> set[str]:
        """Delegate to DocumentLoader.get_supported_extensions."""
        return self.loader.get_supported_extensions()
