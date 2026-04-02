from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


# ── Enums ──────────────────────────────────────────────────────────────

class FileType(str, Enum):
    PDF = "pdf"
    TXT = "txt"
    MD = "md"
    MP3 = "mp3"
    WAV = "wav"
    M4A = "m4a"
    WEBM = "webm"


class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# ── Request Models ─────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000, description="User message")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of documents to retrieve")


# ── Response Models ────────────────────────────────────────────────────

class SourceReference(BaseModel):
    filename: str
    file_type: str
    chunk_index: int
    content_preview: str = Field(description="First 200 chars of the chunk")
    relevance_score: float


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceReference] = []


class DocumentResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    file_size_bytes: int
    status: ProcessingStatus
    chunk_count: int = 0
    uploaded_at: str
    error_message: str | None = None


class UploadResponse(BaseModel):
    id: str
    filename: str
    status: ProcessingStatus
    message: str


class DocumentListResponse(BaseModel):
    documents: list[DocumentResponse]
    total: int


class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str = "1.0.0"
    vector_database_collection: str
    document_count: int
    timestamp: str


class ErrorResponse(BaseModel):
    detail: str


# ── SSE Event Models ──────────────────────────────────────────────────

class StreamEvent(BaseModel):
    event: str = Field(description="Event type: token, sources, done, error")
    data: str = Field(description="Event payload")
