from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    session_id: str | None = None


class ChatResponse(BaseModel):
    answer: str
    places: list[dict[str, Any]]
    total: int | None = None
    session_id: str


class ResetRequest(BaseModel):
    session_id: str


class AgentResult(BaseModel):
    answer: str
    places: list[dict[str, Any]] = Field(default_factory=list)
    total: int | None = None
