"""Loads the MCQ answer key synced by scripts/sync_recall_answer_key.py
(docs/IMPLEMENTATION-quiz-capture-v2.md Step 5.3) — the server's only source of
truth for which lesson recall_questions MCQ option is correct, since the
backend otherwise has zero access to content/roadmaps. Loaded once at import;
re-run the sync script (and redeploy) to pick up new/changed content, the same
freshness model backend/sync_career_templates.py already uses for templates.
"""
import json
from pathlib import Path
from typing import Optional, TypedDict

_PATH = Path(__file__).resolve().parent.parent / "data" / "recall_answer_key.json"

try:
    _MANIFEST: dict = json.loads(_PATH.read_text(encoding="utf-8"))
except (FileNotFoundError, json.JSONDecodeError):
    _MANIFEST = {}


class AnswerKeyEntry(TypedDict):
    correct_index: int
    options_count: int


def lookup(question_served: str) -> Optional[AnswerKeyEntry]:
    """Look up a served item id (e.g. "dsa/quicksort-and-partition#0"). Returns
    None on a miss — the caller must treat that as "cannot verify server-side"
    and fall back gracefully (never guess, never fail the completion)."""
    return _MANIFEST.get(question_served)
