from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.api.deps import CurrentUser
from app.schemas.report import SourceOut
from app.services import knowledge_service

router = APIRouter(prefix="/knowledge", tags=["knowledge"])


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    top_k: int = Field(default=5, ge=1, le=20)


@router.post("/search", response_model=list[SourceOut])
async def search_knowledge(
    payload: KnowledgeSearchRequest,
    user: CurrentUser,
) -> list[SourceOut]:
    """Debug/eval endpoint: run a retrieval query directly against the knowledge base, without
    an analysis or the LLM. Useful for verifying the RAG pipeline independently of report
    generation."""
    result = knowledge_service.search(payload.query, top_k=payload.top_k)
    return [SourceOut(**s) for s in result.as_sources()]
