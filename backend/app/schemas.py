"""
Pydantic models for request/response validation.
"""
from datetime import datetime
from typing import Optional, Literal, Any
from pydantic import BaseModel, Field


# ─── Requests ───────────────────────────────────────────────────────────────

class CreateSessionRequest(BaseModel):
    title: Optional[str] = Field(None, description="Optional session title")
    model_provider: Optional[str] = Field("anthropic", description="LLM provider to use")


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User message (required, non-empty)")


# ─── Responses ──────────────────────────────────────────────────────────────

class SessionResponse(BaseModel):
    id: int
    title: Optional[str]
    model_provider: Optional[str]
    created_at: datetime


class MessageResponse(BaseModel):
    id: int
    session_id: int
    role: str
    content: str
    citations: Optional[Any]
    created_at: datetime


class ArtifactResponse(BaseModel):
    id: int
    type: str
    sanitized_content: Optional[str]
    created_at: datetime


class ConfigResponse(BaseModel):
    llm_provider: str
    ollama_model: str
    ollama_base_url: str


class HealthStatus(BaseModel):
    status: str  # "ok" or "degraded"
    db: str       # "connected" or "unavailable"
    llm_provider: str
    ollama_status: str  # "reachable" | "unreachable" | "not_configured"


# ─── Errors ─────────────────────────────────────────────────────────────────

class ErrorDetail(BaseModel):
    code: int
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail
