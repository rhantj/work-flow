from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class ChecklistGenerateRequest(BaseModel):
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[str] = None
    existing_items: List[str] = Field(default_factory=list)


class ChecklistItemSuggestion(BaseModel):
    title: str
    reason: str = ""


class ChecklistGenerateResponse(BaseModel):
    items: List[ChecklistItemSuggestion]
    engine: str
