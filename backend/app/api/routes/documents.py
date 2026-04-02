"""Document upload, list, and delete endpoints."""

import os
import uuid
import logging
from pathlib import Path

import aiofiles
from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks, HTTPException

from app.config import settings
from app.models.schemas import (
    UploadResponse,
    DocumentListResponse,
    DocumentResponse,
    ProcessingStatus,
)
from app.api.dependencies import get_vector_store, get_document_processor
from app.services.vector_store import VectorStoreService
from app.services.document_processor import DocumentProcessor

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/documents", tags=["documents"])

# In-memory document status tracker (would be a DB in production)
_document_status: dict[str, dict] = {}


async def _process_document_task(
    doc_id: str,
    file_path: Path,
    processor: DocumentProcessor,
    vector_store: VectorStoreService,
):
    """Background task to process and vectorize a document."""
    try:
        _document_status[doc_id]["status"] = ProcessingStatus.PROCESSING

        # Process file into chunks
        chunks = await processor.process_file(file_path, doc_id)

        if not chunks:
            _document_status[doc_id]["status"] = ProcessingStatus.FAILED
            _document_status[doc_id]["error"] = "No content could be extracted"
            return

        # Add to vector store
        await vector_store.add_documents(chunks)

        _document_status[doc_id]["status"] = ProcessingStatus.COMPLETED
        _document_status[doc_id]["chunk_count"] = len(chunks)
        logger.info(f"Document {doc_id} processed successfully: {len(chunks)} chunks")

    except Exception as e:
        logger.error(f"Failed to process document {doc_id}: {e}", exc_info=True)
        _document_status[doc_id]["status"] = ProcessingStatus.FAILED
        _document_status[doc_id]["error"] = str(e)


@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    processor: DocumentProcessor = Depends(get_document_processor),
    vector_store: VectorStoreService = Depends(get_vector_store),
):
    """
    Upload a document for processing and vectorization.

    Supported formats: PDF, TXT, MD, MP3, WAV, M4A, WEBM
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    # Validate file type
    if not processor.is_supported(file.filename):
        supported = ", ".join(sorted(processor.get_supported_extensions()))
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Supported: {supported}",
        )

    # Validate file size
    content = await file.read()
    if len(content) > settings.max_file_size_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE_MB}MB",
        )

    # Save file to disk
    doc_id = str(uuid.uuid4())
    safe_filename = f"{doc_id}_{file.filename}"
    file_path = settings.upload_path / safe_filename

    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)

    # Track document status
    _document_status[doc_id] = {
        "id": doc_id,
        "filename": file.filename,
        "file_type": Path(file.filename).suffix.lstrip(".").lower(),
        "file_size_bytes": len(content),
        "status": ProcessingStatus.PENDING,
        "chunk_count": 0,
        "uploaded_at": file_path.stat().st_ctime,
        "error": None,
    }

    # Process in background
    background_tasks.add_task(
        _process_document_task, doc_id, file_path, processor, vector_store
    )

    return UploadResponse(
        id=doc_id,
        filename=file.filename,
        status=ProcessingStatus.PENDING,
        message="Document uploaded and queued for processing",
    )


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    vector_store: VectorStoreService = Depends(get_vector_store),
):
    """List all uploaded documents with their processing status."""
    # Merge in-memory status with vector store metadata
    vector_docs = await vector_store.get_documents_metadata()
    vector_docs_map = {d["doc_id"]: d for d in vector_docs}

    documents: list[DocumentResponse] = []

    for doc_id, info in _document_status.items():
        vec_info = vector_docs_map.get(doc_id, {})
        chunk_count = vec_info.get("chunk_count", info.get("chunk_count", 0))

        documents.append(DocumentResponse(
            id=doc_id,
            filename=info["filename"],
            file_type=info["file_type"],
            file_size_bytes=info["file_size_bytes"],
            status=info["status"],
            chunk_count=chunk_count,
            uploaded_at=vec_info.get("uploaded_at", str(info.get("uploaded_at", ""))),
            error_message=info.get("error"),
        ))

    # Sort by upload time (newest first)
    documents.sort(key=lambda d: d.uploaded_at, reverse=True)

    return DocumentListResponse(documents=documents, total=len(documents))


@router.delete("/{doc_id}")
async def delete_document(
    doc_id: str,
    vector_store: VectorStoreService = Depends(get_vector_store),
):
    """Delete a document and all its vector chunks."""
    if doc_id not in _document_status:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete from vector store
    deleted = await vector_store.delete_by_doc_id(doc_id)

    # Delete file from disk
    info = _document_status[doc_id]
    upload_dir = settings.upload_path
    for f in upload_dir.iterdir():
        if f.name.startswith(doc_id):
            os.remove(f)
            break

    # Remove from status tracker
    del _document_status[doc_id]

    return {"message": f"Document deleted. {deleted} chunks removed."}


@router.get("/{doc_id}/status")
async def get_document_status(doc_id: str):
    """Get the processing status of a specific document."""
    if doc_id not in _document_status:
        raise HTTPException(status_code=404, detail="Document not found")

    info = _document_status[doc_id]
    return DocumentResponse(
        id=doc_id,
        filename=info["filename"],
        file_type=info["file_type"],
        file_size_bytes=info["file_size_bytes"],
        status=info["status"],
        chunk_count=info.get("chunk_count", 0),
        uploaded_at=str(info.get("uploaded_at", "")),
        error_message=info.get("error"),
    )
