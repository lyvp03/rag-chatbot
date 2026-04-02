"""RAG chat service: retrieves context and streams LLM responses."""

import json
import logging
from typing import AsyncIterator

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from app.config import settings
from app.core.prompts import RAG_SYSTEM_PROMPT
from app.services.vector_store import VectorStoreService
from app.models.schemas import SourceReference

logger = logging.getLogger(__name__)


class ChatService:
    """Handles RAG-based chat: retrieves relevant context and streams LLM answers."""

    def __init__(self, vector_store: VectorStoreService):
        self.vector_store = vector_store
        self.llm = ChatOpenAI(
            model=settings.LLM_MODEL,
            temperature=settings.LLM_TEMPERATURE,
            api_key=settings.LLM_API_KEY,           
            base_url=settings.LLM_API_BASE,          
            streaming=True,
        )
        self.prompt = ChatPromptTemplate.from_template(RAG_SYSTEM_PROMPT)
        self.chain = self.prompt | self.llm | StrOutputParser()

    async def chat_stream(
        self, message: str, top_k: int = 5
    ) -> AsyncIterator[str]:
        """
        Process a user message through the RAG pipeline and stream the response as SSE events.

        Yields SSE-formatted strings:
            - event: token  -> incremental answer tokens
            - event: sources -> JSON array of source references
            - event: done   -> stream complete
            - event: error  -> error message

        Args:
            message: The user's question.
            top_k: Number of context chunks to retrieve.
        """
        try:
            # Step 1: Retrieve relevant documents
            results = await self.vector_store.similarity_search(message, k=top_k)

            if not results:
                yield self._sse("token", "I don't have any documents to reference. Please upload some documents first, then ask your question again.")
                yield self._sse("sources", "[]")
                yield self._sse("done", "")
                return

            # Step 2: Build context string and source references
            
            context_parts = []
            sources: list[SourceReference] = []

            for i, (doc, score) in enumerate(results):
                meta = doc.metadata
                context_parts.append(
                    f"[{i+1}] {meta.get('filename', 'unknown')} | Chunk {meta.get('chunk_index', 0)}\n"
                    f"{doc.page_content}"
                )
                sources.append(SourceReference(
                    filename=meta.get("filename", "unknown"),
                    file_type=meta.get("file_type", "unknown"),
                    chunk_index=meta.get("chunk_index", 0),
                    content_preview=doc.page_content[:200],
                    relevance_score=round(float(score), 4),
                ))

            # Step 3: Send source references
            sources_json = json.dumps(
                [s.model_dump() for s in sources], ensure_ascii=False
            )
            yield self._sse("sources", sources_json)
            context = "\n\n---\n\n".join(context_parts) 
            # Step 4: Stream LLM response
            async for token in self.chain.astream(
                {"context": context, "question": message}
            ):
                yield self._sse("token", token)

            yield self._sse("done", "")

        except Exception as e:
            logger.error(f"Chat stream error: {e}", exc_info=True)
            yield self._sse("error", str(e))

    
    @staticmethod
    def _sse(event: str, data: str) -> str:
        lines = "\n".join(f"data: {line}" for line in data.split("\n"))
        return f"event: {event}\n{lines}\n\n"