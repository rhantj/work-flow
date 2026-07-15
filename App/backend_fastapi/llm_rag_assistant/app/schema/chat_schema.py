from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class RagIngestRequest(BaseModel):
    project_id: int
    source_type: Literal["meeting", "task"]
    source_id: int
    content: str


class RagIngestResponse(BaseModel):
    chunk_ids: list[int]
    chunk_count: int
