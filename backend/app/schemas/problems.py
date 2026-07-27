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
