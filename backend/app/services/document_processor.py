"""Document processing service: loads, chunks, and prepares documents for vectorization."""

import logging
import chardet
from pathlib import Path
from datetime import datetime, timezone

from langchain_core.documents import Document
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    UnstructuredMarkdownLoader,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from chonkie import SemanticChunker

from app.config import settings
from app.services.audio_processor import AudioProcessor, SUPPORTED_AUDIO_EXTENSIONS

logger = logging.getLogger(__name__)

# Mapping of file extensions to their loader classes
TEXT_LOADERS = {
    ".pdf": PyPDFLoader,
    ".md": UnstructuredMarkdownLoader,
}

# File using semantic chunking
SEMANTIC_EXTENSIONS={".txt"}


class DocumentProcessor:
    """Processes uploaded files into chunked LangChain Documents."""

    def __init__(self):
        self.audio_processor = AudioProcessor()
        #Semantic chunker for pdf and txt files
        self.semantic_chunker=SemanticChunker(
            embedding_model="minishlab/potion-base-8M",
            threshold=0.7,
            chunk_size=512
        )

        #Fixed chunker - fallback for MD, audio
        self.fixed_chunker = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    @staticmethod
    def get_supported_extensions() -> set[str]:
        """Return all supported file extensions."""
        return set(TEXT_LOADERS.keys()) | SUPPORTED_AUDIO_EXTENSIONS

    @staticmethod
    def is_supported(filename: str) -> bool:
        """Check if a file type is supported."""
        suffix = Path(filename).suffix.lower()
        return suffix in TEXT_LOADERS or suffix in SUPPORTED_AUDIO_EXTENSIONS or suffix in SEMANTIC_EXTENSIONS

    def _chunk_documents(self, raw_documents:list[Document], suffix:str)->list:
        """
        Chunk documents using semantic or fixed strategy based on file type.

        Args:
            raw_documents: Raw documents loaded from file.
            suffix: File extension(".pdf", ",txt")
        
        Return:
            List of chunked document
        """
        # Merge all text into 1 string
        full_text="\n\n".join(doc.page_content for doc in raw_documents)

        if suffix in SEMANTIC_EXTENSIONS:
            logger.info(f"Using semantic chunking for {suffix}")
            try:
                #Chonkie return list[Chunk], convert to Document
                chonkie_chunks=self.semantic_chunker.chunk(full_text)
                return[
                    Document(page_content=chunk.text)
                    for chunk in chonkie_chunks
                    if chunk.text.strip()
                ]
            except Exception as e:
                #If semantic chunking error -> fallback fixed
                logger.warning(f"Semantic chunking failed: {e} - falling back to fixed chunking")
                return self.fixed_chunker.split_documents(raw_documents)
        else:
            logger.info(f"Using fixed chunking for {suffix}")
            return self.fixed_chunker.split_documents(raw_documents)

    async def process_file(self, file_path: Path, doc_id:str)->list:
        """
        Process a file into chunked Documents ready for vectorization.

        Args:
            file_path: Path to upload the file
            doc_id: Unique document identifier for metadata tracking.

        Returns:
            List of chunked Document objects with enriched metadata
        """
        suffix=file_path.suffix.lower()
        filename=file_path.name
        timestamp=datetime.now(timezone.utc).isoformat()

        logger.info(f"Processing file: {filename} (type: {suffix})")

        #Step 1: Load raw documents
        if suffix in SUPPORTED_AUDIO_EXTENSIONS:
            raw_documents=[await self.audio_processor.transcribe(file_path)]
        
        elif suffix == ".txt":
            # Auto detect encoding
            with open(file_path, "rb") as f:
                detected = chardet.detect(f.read())
            encoding = detected.get("encoding", "utf-8") or "utf-8"
            logger.info(f"Detected encoding: {encoding}")
            loader = TextLoader(str(file_path), encoding=encoding)
            raw_documents = loader.load()

        elif suffix in TEXT_LOADERS:
            loader_cls=TEXT_LOADERS[suffix]
            loader=loader_cls(str(file_path))
            raw_documents=loader.load()
        else:
            raise ValueError(f"Unsupported file type: {suffix}")

        if not raw_documents:
            logger.warning(f"No content extracted from {filename}")
            return []

        #Step 2: Chunk - semantic or fixed
        chunks = self._chunk_documents(raw_documents, suffix)

        """
        # DEBUG: Print chunks
        print(f"\n{'='*60}")
        print(f"FILE: {filename} | TOTAL CHUNKS: {len(chunks)}")
        print(f"{'='*60}")
        for i, chunk in enumerate(chunks):
            print(f"\n--- CHUNK {i+1}/{len(chunks)} ---")
            print(f"Length: {len(chunk.page_content)} chars")
            print(f"Content:\n{chunk.page_content[:300]}...")  # 300 ký tự đầu
            print(f"{'-'*40}")
        print(f"{'='*60}\n")

        """

        if not chunks:
            logger.warning(f"No chunks created from {filename}")
            return []

        #Step 3: Enrich metadata
        for i, chunk in enumerate(chunks):
            chunk.metadata.update({
                "doc_id": doc_id,
                "filename": filename,
                "file_type": suffix.lstrip("."),
                "chunk_index":i,
                "total_chunks":len(chunks),
                "uploaded_at":timestamp,
                "chunking_strategy": "semantic" if suffix in SEMANTIC_EXTENSIONS else "fixed"
            })

        logger.info(f"Processed {filename}: {len(chunks)} chunks ({chunks[0].metadata['chunking_strategy']})") 
        return chunks

        