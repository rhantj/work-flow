from __future__ import annotations

from fastapi import APIRouter, Depends

from core.db import get_pool
from llm_rag_assistant.app.schema.chat_schema import RagIngestRequest, RagIngestResponse
from llm_rag_assistant.app.services.ingestion_service import ingest_content

router = APIRouter(prefix="/ai/rag", tags=["rag"])


@router.post("/ingest", response_model=RagIngestResponse)
async def ingest(request: RagIngestRequest, pool=Depends(get_pool)) -> RagIngestResponse:
    return await ingest_content(
        pool, request.project_id, request.source_type, request.source_id, request.content
    )
