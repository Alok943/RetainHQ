from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, ConfigDict, Field
import uuid
from .activity import ActivityResponse

class ReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    activity_id: uuid.UUID
    status: str
    scheduled_for: datetime
    completed_at: Optional[datetime] = None
    rating: Optional[str] = None
    recalled: Optional[bool] = None
    # LLM grader output (proposal); user's rating/recalled stay authoritative.
    ai_verdict: Optional[str] = None
    ai_recalled: Optional[bool] = None
    ai_feedback: Optional[str] = None
    created_at: datetime

    activity: ActivityResponse

class ReviewComplete(BaseModel):
    # Subjective signal: how hard it felt. Constrained to the documented scale.
    rating: Literal["easy", "medium", "hard"]
    # Objective signal: did they actually reconstruct the answer? (got-it / missed-it)
    recalled: Optional[bool] = None

class ReviewGradeRequest(BaseModel):
    # The user's free-recall attempt. Capped to bound LLM cost/latency.
    answer: str = Field(default="", max_length=4000)

class RelatedSubtopic(BaseModel):
    # A suggested adjacent topic to learn next — never part of the grade.
    title: str
    explainer: str

class ReviewGradeResponse(BaseModel):
    verdict: Literal["correct", "partial", "incorrect"]
    recalled: bool
    feedback: str
    revision_note: str
    related_subtopics: list[RelatedSubtopic] = []


# --- Question mode (prototype, gated behind GRADER_ENABLED) ----------------- #

class ReviewQuestionsResponse(BaseModel):
    # 2-3 LLM-generated short-answer questions grounded in the activity's key_memory.
    questions: list[str]

class QAPair(BaseModel):
    question: str = Field(max_length=600)
    answer: str = Field(default="", max_length=2000)

class ReviewGradeQuestionsRequest(BaseModel):
    answers: list[QAPair] = Field(max_length=5)

class QuestionItemResult(BaseModel):
    question: str
    correct: bool
    note: str

class ReviewGradeQuestionsResponse(BaseModel):
    recalled: bool
    feedback: str
    items: list[QuestionItemResult]
    related_subtopics: list[RelatedSubtopic] = []
