from datetime import datetime
from typing import Any, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field, Extra

class CompanionSessionPayload(BaseModel):
    """
    Metadata about the session classification.
    extra='forbid' is a critical security invariant (SPEC-companion-phase1 §6):
    It prevents any raw chat content or unbounded text fields from being accidentally
    persisted to the database.
    """
    sources: List[str] = Field(description="List of domains or app surfaces e.g. ['leetcode.com', 'claude.ai']")
    study_type: Optional[str] = None
    assistance_level: Optional[str] = None
    confidence_band: Optional[str] = None
    candidates: Optional[List[dict]] = None
    reason: Optional[str] = None
    title_sample: Optional[str] = Field(None, max_length=500, description="Capped sample of window titles")
    classifier: Optional[str] = None
    prompt_version: Optional[str] = None
    embedding_model: Optional[str] = None

    class Config:
        extra = "forbid"


class CompanionSessionIn(BaseModel):
    """
    One completed study session from the browser extension.
    """
    session_id: UUID = Field(description="Idempotency key for deduplication")
    node_id: Optional[UUID] = Field(None, description="Matched roadmap node; None means it goes to triage")
    duration_min: int = Field(..., ge=0)
    occurred_at: datetime = Field(description="When the session ended (stitcher's `end`), not when it synced — sessions sync in batches after offline gaps")
    payload: CompanionSessionPayload


class CompanionBatchIn(BaseModel):
    """
    Batch of sessions to sync.
    """
    sessions: List[CompanionSessionIn]
