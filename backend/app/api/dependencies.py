"""Shared dependencies for API routes (dependency injection)."""

from functools import lru_cache

from app.services.vector_store import VectorStoreService
from app.services.document_processor import DocumentProcessor
from app.services.chat_service import ChatService


@lru_cache()
def get_vector_store() -> VectorStoreService:
    """Singleton VectorStoreService instance."""
    return VectorStoreService()


@lru_cache()
def get_document_processor() -> DocumentProcessor:
    """Singleton DocumentProcessor instance."""
    return DocumentProcessor()


def get_chat_service() -> ChatService:
    """Get ChatService instance (depends on VectorStoreService)."""
    return ChatService(vector_store=get_vector_store())
