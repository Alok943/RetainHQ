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
    duration_ms: Optional[int] = None
    created_at: datetime

    # Quiz v2 persisted fields (Step 5.5) — real Review columns, all nullable.
    mode: Optional[str] = None
    question_format: Optional[str] = None
    question_tier: Optional[str] = None
    question_source: Optional[str] = None
    question_served: Optional[str] = None
    hint_used: Optional[bool] = None
    think_ms: Optional[int] = None

    # Attached fields for lesson card resolution
    roadmap_slug: Optional[str] = None
    node_title: Optional[str] = None

    # Quiz v2 (docs/IMPLEMENTATION-quiz-capture-v2.md Step 5.1/5.4) — attached,
    # not real ORM columns on Review. `topic_key`/`topic_label` group/order the
    # due queue by topic (services/topic_key.py). `last_question_served` is the
    # most recent COMPLETED review's `question_served` for this same activity,
    # so the client can avoid repeating the same item this session.
    topic_key: Optional[str] = None
    topic_label: Optional[str] = None
    last_question_served: Optional[str] = None

    activity: ActivityResponse

class ReviewComplete(BaseModel):
    # Subjective signal: how hard it felt. Constrained to the documented scale.
    # For an MCQ completion verified server-side, this is a client HINT only —
    # the server derives the real rating/recalled from its own verification
    # (see complete_review) and ignores what's sent here in that path.
    rating: Literal["easy", "medium", "hard"]
    # Objective signal: did they actually reconstruct the answer? (got-it / missed-it)
    recalled: Optional[bool] = None
    # Client-measured wall-clock (performance.now() delta, card-shown to
    # outcome-submitted). Server clamps to (0, 1_800_000] — anything outside
    # that lands as NULL rather than failing the completion.
    duration_ms: Optional[int] = None

    # --- Quiz v2 (Step 5.5), all optional — old clients keep working unchanged ---
    mode: Optional[Literal["quick", "typed"]] = None
    question_format: Optional[Literal["mcq", "typed", "free"]] = None
    question_tier: Optional[Literal["tier1", "tier2", "tier3"]] = None
    question_source: Optional[Literal["lesson", "question_set", "none"]] = None
    # Stable id of the specific item served, e.g. "<roadmap>/<slug>#<index>".
    question_served: Optional[str] = Field(default=None, max_length=200)
    hint_used: bool = False
    think_ms: Optional[int] = None

    # Input-only (never persisted as its own column): which option the learner
    # picked, as an index into the AUTHORED (pre-shuffle) options array. None
    # means "I don't know". Only meaningful when question_format == "mcq" —
    # ignored otherwise. The server looks this up against its own synced
    # answer key (services/recall_answer_key.py) rather than trusting a
    # client-computed `correct` — see complete_review.
    selected_option_index: Optional[int] = None

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


# --- Question mode (gated behind GRADER_ENABLED) ---------------------------- #

class ReviewQuestionsRequest(BaseModel):
    # How the user chose to revise this session: 'main' = core points only,
    # 'deep' = adds apply/derive/compare/edge-case probes.
    depth: Literal["main", "deep"] = "main"

class ReviewQuestionsResponse(BaseModel):
    # LLM-generated short-answer questions, served SHUFFLED from a persisted set
    # (reused across QUESTION_SET_REUSE sessions). Reference answers stay
    # server-side — only the question text goes to the client.
    questions: list[str]
    depth: Literal["main", "deep"] = "main"

class QAPair(BaseModel):
    question: str = Field(max_length=600)
    answer: str = Field(default="", max_length=2000)
    reference_answer: Optional[str] = None

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
