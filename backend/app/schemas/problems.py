from typing import Optional
from pydantic import BaseModel, ConfigDict
import uuid


class ProblemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    external_id: int
    slug: str
    title: str
    difficulty: str  # 'easy' | 'medium' | 'hard'
    url: Optional[str] = None
    paid_only: bool = False
    role: str  # 'primary' | 'supporting' | 'alternative'
    marked_status: Optional[str] = None  # 'solved' | 'attempted' | None (unmarked)


class ProblemMarkIn(BaseModel):
    status: str = "solved"  # 'solved' | 'attempted'


class ProblemSearchOut(BaseModel):
    id: uuid.UUID
    external_id: int
    title: str
    slug: str
    difficulty: str
    url: Optional[str] = None
    paid_only: bool = False
    node_id: Optional[uuid.UUID] = None
    node_title: Optional[str] = None
    confidence_band: Optional[str] = None
    already_logged: bool = False
    reason: Optional[str] = None
