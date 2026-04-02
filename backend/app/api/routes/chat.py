"""Chat endpoint with streaming SSE responses."""

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.models.schemas import ChatRequest
from app.api.dependencies import get_chat_service
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("")
async def chat(
    request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service),
):
    """
    Send a message and receive a streaming RAG response.

    Returns a Server-Sent Events (SSE) stream with the following event types:
    - `sources`: JSON array of source document references (sent first)
    - `token`: Incremental answer text tokens
    - `done`: Stream complete signal
    - `error`: Error message if something goes wrong
    """
    return StreamingResponse(
        chat_service.chat_stream(
            message=request.message,
            top_k=request.top_k,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
