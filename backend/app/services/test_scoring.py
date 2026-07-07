"""Test-session scoring (SPEC-test-runtime.md). Pure, auditable, no hidden state —
gamification/leaderboard features can read `score`/`max_score` later without ever
touching the grading path itself.

    got, non-trap:      +10
    got, trap:          +15   (bonus for defeating an engineered trap)
    missed:               0   (no penalty — honesty must never cost more than a guess)
    wrong, non-MCQ:       0   (a genuine attempt that missed isn't punished further)
    wrong, MCQ:          -5   (guess penalty — offsets ~25% guess odds so E[guessing] < 0)

`missed` scoring 0 (not negative) alongside `wrong` non-MCQ scoring 0 is deliberate: skipping
honestly must never be worse than attempting and missing, or the format teaches students to guess
rather than say "I don't know".
"""
from typing import Iterable, Protocol


class _Result(Protocol):
    type: str
    outcome: str
    trap: bool


POINTS_GOT = 10
POINTS_GOT_TRAP_BONUS = 15
POINTS_WRONG_MCQ = -5


def score_question(result: _Result) -> int:
    if result.outcome == "got":
        return POINTS_GOT_TRAP_BONUS if result.trap else POINTS_GOT
    if result.outcome == "wrong" and result.type == "mcq":
        return POINTS_WRONG_MCQ
    return 0  # missed, or wrong on a non-MCQ type


def max_question_points(result: _Result) -> int:
    return POINTS_GOT_TRAP_BONUS if result.trap else POINTS_GOT


def score_attempt(results: Iterable[_Result]) -> tuple[int, int]:
    """Returns (score, max_score) for a whole submitted session."""
    results = list(results)
    score = sum(score_question(r) for r in results)
    max_score = sum(max_question_points(r) for r in results)
    return score, max_score
