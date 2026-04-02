"""FastAPI application entry point."""
import os
os.environ["PATH"] += r";C:\Users\Admin\AppData\Local\Microsoft\WinGet\Links"
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.routes import health, documents, chat

# ── Logging ────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ── Lifespan ───────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    logger.info("🚀 Starting RAG API server...")
    logger.info(f"   Vector DB path: {settings.faiss_path}")
    logger.info(f"   Upload dir:    {settings.upload_path}")
    logger.info(f"   LLM model:     {settings.LLM_MODEL}")
    logger.info(f"   Embedding:     {settings.EMBEDDING_MODEL}")

    # Ensure directories exist
    settings.upload_path.mkdir(parents=True, exist_ok=True)
    settings.faiss_path.mkdir(parents=True, exist_ok=True)

    yield

    logger.info("🛑 Shutting down RAG API server...")


# ── App ────────────────────────────────────────────────────────────────

app = FastAPI(
    title="RAG API",
    description="Retrieval-Augmented Generation API with document processing and chat",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ───────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ─────────────────────────────────────────────────────────────

app.include_router(health.router, prefix="/api")
app.include_router(documents.router, prefix="/api")
app.include_router(chat.router, prefix="/api")


@app.get("/")
async def root():
    """Root redirect to API docs."""
    return {
        "message": "RAG API is running",
        "docs": "/docs",
        "health": "/api/health",
    }
