"""Dataset case schemas — pure Pydantic, no `app.*` imports.

Kept dependency-free of the FastAPI app so `tests/test_eval_datasets.py` can
validate dataset shape without pulling in DB/settings machinery.
"""
from typing import Literal, Optional
from pydantic import BaseModel, Field


class GraderCase(BaseModel):
    """One case for the `grader` suite — exercises services/grader.grade_recall."""
    id: str
    category: Literal[
        "paraphrase_correct", "confidently_wrong", "partial", "empty", "off_topic", "injection"
    ]
    question: str
    reference_answer: str
    user_answer: str
    expected: Literal["correct", "partial", "incorrect"]
    reviewed: bool = False


class MCQOption(BaseModel):
    text: str
    correct: bool
    why: str


class MCQItemCase(BaseModel):
    """One case for the `mcq_items` suite — a candidate MCQ item to validate."""
    id: str
    question: str
    context: Optional[dict] = None
    # Eval-authoring signal (not part of the real content schema): does this
    # question require the context block to be answerable? Drives the
    # "context present when the question references data" structural check.
    references_data: bool = False
    options: list[MCQOption] = Field(min_length=4, max_length=4)
    reviewed: bool = False


class AnswerableCase(BaseModel):
    """One case for the `answerable` suite — judged for "answerable without the lesson open"."""
    id: str
    question: str
    context: Optional[dict] = None
    answer: str  # reference material for the judge; never shown to a learner
    # What this case is *expected* to judge as, for reporting/debugging only —
    # the suite's pass bar is the raw yes-rate across all cases, not agreement
    # with this field (see IMPLEMENTATION-quiz-capture-v2.md Step 2).
    expected_answerable: bool = True
    reviewed: bool = False


class LeetcodeStatementCase(BaseModel):
    """One case for the `leetcode_statements` suite — hand-authored key facts to check a
    generated statement against. The generator itself doesn't exist yet (Step 7); this
    dataset is seeded now so the suite is ready the moment it does."""
    id: str
    problem_slug: str
    problem_title: str
    difficulty: Literal["easy", "medium", "hard"]
    key_facts: dict  # {goal, input, output, constraint} — plain strings
    reviewed: bool = False


SUITE_SCHEMAS = {
    "grader": GraderCase,
    "mcq_items": MCQItemCase,
    "answerable": AnswerableCase,
    "leetcode_statements": LeetcodeStatementCase,
}
