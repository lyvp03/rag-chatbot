"""Health check endpoint."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from app.config import settings
from app.models.schemas import HealthResponse
from app.api.dependencies import get_vector_store
from app.services.vector_store import VectorStoreService

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check(
    vector_store: VectorStoreService = Depends(get_vector_store),
):
    """Check service health and vector database status."""
    stats = await vector_store.get_collection_stats()
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        vector_database_collection="faiss_index",   
        document_count=stats["total_chunks"],
        timestamp=datetime.now(timezone.utc).isoformat(),
    )