"""
Handles all file-loading logic for the RAG pipeline.
Supports: PDF (pdfplumber), TXT, Markdown, and audio files.
"""

import logging
import chardet
from pathlib import Path

from langchain_core.documents import Document
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    UnstructuredMarkdownLoader,
)

from app.services.audio_processor import AudioProcessor, SUPPORTED_AUDIO_EXTENSIONS

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Extension configuration
# ---------------------------------------------------------------------------

TEXT_LOADERS = {
    ".pdf": PyPDFLoader,
    ".md":  UnstructuredMarkdownLoader,
}

SEMANTIC_EXTENSIONS    = {".txt"}
STRUCTURED_EXTENSIONS  = {".md"}


class DocumentLoader:
    """Loads files into raw LangChain Documents, dispatching by file type."""

    def __init__(self):
        self.audio_processor = AudioProcessor()

    # -----------------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------------

    async def load(self, file_path: Path) -> list[Document]:
        """
        Load a file and return a list of raw Documents.

        Dispatches to the correct loader based on file extension.
        Raises ValueError for unsupported types.
        """
        suffix = file_path.suffix.lower()
        logger.info(f"Loading file: {file_path.name} (type: {suffix})")

        if suffix in SUPPORTED_AUDIO_EXTENSIONS:
            return await self._load_audio(file_path)
        elif suffix == ".txt":
            return self._load_txt(file_path)
        elif suffix == ".pdf":
            return self._load_pdf(file_path)
        elif suffix in TEXT_LOADERS:
            return self._load_generic(file_path, suffix)
        else:
            raise ValueError(f"Unsupported file type: {suffix}")

    @staticmethod
    def is_supported(filename: str) -> bool:
        """Return True if the file extension is supported."""
        suffix = Path(filename).suffix.lower()
        return (
            suffix in TEXT_LOADERS
            or suffix in SUPPORTED_AUDIO_EXTENSIONS
            or suffix in SEMANTIC_EXTENSIONS
        )

    @staticmethod
    def get_supported_extensions() -> set[str]:
        """Return the set of all supported file extensions."""
        return set(TEXT_LOADERS.keys()) | SUPPORTED_AUDIO_EXTENSIONS | SEMANTIC_EXTENSIONS

    # -----------------------------------------------------------------------
    # Private loaders
    # -----------------------------------------------------------------------

    async def _load_audio(self, file_path: Path) -> list[Document]:
        """Transcribe audio via Whisper and return as a single Document."""
        doc = await self.audio_processor.transcribe(file_path)
        return [doc]

    def _load_txt(self, file_path: Path) -> list[Document]:
        """Load .txt with auto-detected encoding."""
        with open(file_path, "rb") as f:
            detected = chardet.detect(f.read())
        encoding = detected.get("encoding", "utf-8") or "utf-8"
        logger.info(f"Detected encoding for {file_path.name}: {encoding}")
        return TextLoader(str(file_path), encoding=encoding).load()

    def _load_pdf(self, file_path: Path) -> list[Document]:
        """
        Load a PDF with pdfplumber.

        - Plain text  → Document(chunk_type="text")
        - Tables      → Markdown-formatted Document(chunk_type="table")

        Falls back to PyPDFLoader if pdfplumber is unavailable or errors.
        """
        if not PDFPLUMBER_AVAILABLE:
            logger.warning("pdfplumber not installed – falling back to PyPDFLoader")
            return PyPDFLoader(str(file_path)).load()

        documents: list[Document] = []

        try:
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages, start=1):

                    # ── Extract tables ───────────────────────────────────
                    table_bboxes = []
                    for table in page.find_tables():
                        data = table.extract()
                        if not data:
                            continue

                        table_bboxes.append(table.bbox)

                        headers   = [cell or "" for cell in data[0]]
                        separator = ["---"] * len(headers)
                        body_rows = [[cell or "" for cell in row] for row in data[1:]]

                        md_lines = (
                            ["| " + " | ".join(headers)   + " |"]
                            + ["| " + " | ".join(separator) + " |"]
                            + ["| " + " | ".join(row)       + " |" for row in body_rows]
                        )

                        documents.append(
                            Document(
                                page_content="\n".join(md_lines),
                                metadata={
                                    "page":       page_num,
                                    "chunk_type": "table",
                                    "section":    "Table",
                                },
                            )
                        )

                    # ── Extract plain text (exclude table regions) ───────
                    remaining = page
                    for bbox in table_bboxes:
                        try:
                            remaining = remaining.outside_bbox(bbox)
                        except Exception:
                            pass

                    text = (remaining.extract_text() or "").strip()
                    if text:
                        documents.append(
                            Document(
                                page_content=text,
                                metadata={
                                    "page":       page_num,
                                    "chunk_type": "text",
                                    "section":    "Unknown",
                                },
                            )
                        )

        except Exception as exc:
            logger.warning(f"pdfplumber failed ({exc}) – falling back to PyPDFLoader")
            return PyPDFLoader(str(file_path)).load()

        return documents

    def _load_generic(self, file_path: Path, suffix: str) -> list[Document]:
        """Load any file type registered in TEXT_LOADERS."""
        loader_cls = TEXT_LOADERS[suffix]
        return loader_cls(str(file_path)).load()
