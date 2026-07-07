from datetime import datetime
from typing import Literal, Optional, List
from pydantic import BaseModel, ConfigDict, Field
import uuid

# --- /weights: per-node sampling signal ------------------------------------ #

class NodeWeight(BaseModel):
    node_title: str
    due: bool = False               # this node's Activity has an OPEN review due now/overdue
    overdue_days: int = 0
    accuracy_recent: Optional[float] = None  # fraction 'got' over the last ~10 attempts touching this node, or None if untested
    attempts_recent: int = 0


class WeightsResponse(BaseModel):
    nodes: List[NodeWeight]


# --- /grade-fillup: the one LLM call in the whole system -------------------- #

class GradeFillupRequest(BaseModel):
    question: str = Field(max_length=600)
    reference_answer: str = Field(max_length=2000)
    student_answer: str = Field(default="", max_length=1000)


class GradeFillupResponse(BaseModel):
    verdict: Literal["correct", "partial", "incorrect"]
    feedback: str


# --- /attempts: submit a completed session --------------------------------- #

class QuestionResult(BaseModel):
    question_id: str
    node_title: str
    type: Literal["fillup", "numeric", "code-output", "code-fix", "code-write", "query-write", "mcq"]
    outcome: Literal["got", "missed", "wrong"]
    trap: bool = False
    misconception: Optional[str] = None


class SubmitAttemptRequest(BaseModel):
    roadmap_slug: str
    phase: str
    results: List[QuestionResult] = Field(min_length=1, max_length=40)


class SubmitAttemptResponse(BaseModel):
    id: uuid.UUID
    score: int
    max_score: int
    rescheduled_nodes: List[str] = []  # node titles whose FSRS card was pulled forward


class TestAttemptResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    roadmap_id: uuid.UUID
    phase: str
    score: int
    max_score: int
    created_at: datetime
