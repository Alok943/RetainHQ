from datetime import datetime, timedelta
from typing import Optional
import math

from app.models.models import Activity, Review

# FSRS spaced-repetition scheduling (the successor to SM-2).
#
# Each Activity is one "card" carrying its own memory state. Where SM-2 used a
# fixed ease ladder (ease_factor/repetitions/interval_days), FSRS models two
# continuous variables per card:
#   - stability  : how many days until predicted recall decays to the target
#   - difficulty : 1-10, how hard the card is intrinsically
# Each completed review updates both from the ELAPSED time since the last review
# and the grade, then the next interval is chosen so predicted recall equals
# DESIRED_RETENTION. Published studies put FSRS at ~30% fewer reviews than SM-2
# for the same retention, because well-remembered cards space out faster and
# shaky ones come back sooner instead of marching a fixed 1->6->x ladder.
#
# State lives on the Activity: `stability`/`difficulty` are NULL until the first
# GRADED review (a brand-new card has no memory state yet) -> NULL == "new card".
# The legacy SM-2 columns (ease_factor/repetitions) are still written so the
# NOT NULL constraints stay satisfied and old rows keep working; interval_days,
# last_reviewed_at and next_review_at remain the live, meaningful fields.
#
# Invariant (unchanged): an activity in rotation has exactly one open
# status='due' review. apply_fsrs() builds the next review before the caller
# commits, so completion + next review land in the same transaction.

DEFAULT_EASE_FACTOR = 2.5  # legacy SM-2 column; still written to satisfy NOT NULL

# Max reviews surfaced (and counted as "due") in a single day. Overdue cards
# beyond this stay status='due' and roll forward to later sessions — the queue
# is ordered oldest-first — so a user who falls behind always sees a bounded,
# finishable session instead of a demoralizing backlog. An unbounded "23 due"
# count is the classic SRS death spiral: people see it and stop opening the app.
REVIEW_SESSION_CAP = 10


def initial_review_for_activity(
    activity: Activity, now: Optional[datetime] = None, immediate: bool = False
) -> Review:
    """
    Initialize an activity's scheduling state and return its first review.

    Default (immediate=False): the first review is scheduled for TOMORROW (+1 day).
    Quizzing a topic seconds after logging it measures short-term memory, not
    retention, and a batch of log-then-quiz prompts is the main source of review
    fatigue (log 4 topics -> 4 instant exams). The forgetting curve only starts
    to bite after a delay, so the first recall is worth far more a day later.

    immediate=True: schedule the first review NOW. This is the one-time onboarding
    demo for a user's very FIRST activity — a brand-new user sees the recall loop
    instantly (our activation funnel leaks right after the first capture). It's a
    single demo card, not a per-log behavior, so it doesn't reintroduce fatigue.

    The card carries NO FSRS memory state yet (stability/difficulty stay NULL):
    those are established by the FIRST graded review, which is exactly how FSRS
    initializes a card from its opening grade. Every logged activity enters the
    rotation (no difficulty/hint gate). The activity must be flushed so it has an
    id before calling this.
    """
    now = now or datetime.utcnow()
    activity.ease_factor = DEFAULT_EASE_FACTOR  # legacy column, kept populated
    if immediate:
        activity.repetitions = 0
        activity.interval_days = 0
        due_at = now
    else:
        activity.repetitions = 1
        activity.interval_days = 1
        due_at = now + timedelta(days=1)
    activity.next_review_at = due_at
    return Review(
        user_id=activity.user_id,
        activity_id=activity.id,
        status="due",
        scheduled_for=due_at,
    )


def quality_from_outcome(rating: str, recalled: Optional[bool]) -> int:
    """
    Map RetainHQ's two review signals onto an SM-2-style quality grade (0-5).
    Retained purely to persist the `reviews.quality` column for analytics
    continuity — FSRS itself uses fsrs_rating_from_outcome() for scheduling.
      recalled is False        -> 2  (lapse: failed to reconstruct)
      recalled (True/None) + rating:
        'hard'   -> 3
        'medium' -> 4
        'easy'   -> 5
    Only an explicit recalled == False is a failure; a missing recalled
    (older clients) is treated as recalled and graded by the felt rating.
    """
    if recalled is False:
        return 2
    return {"hard": 3, "medium": 4, "easy": 5}.get(rating, 4)


# ---------------------------------------------------------------------------
# FSRS-4.5 core
#
# Published default parameters (open-spaced-repetition). 19 weights. Constants
# are chosen so the interval at DESIRED_RETENTION equals the stability in days.
# ---------------------------------------------------------------------------

FSRS_WEIGHTS = (
    0.4072, 1.1829, 3.1262, 15.4722, 7.2102, 0.5316, 1.0651, 0.0234,
    1.616, 0.1544, 1.0824, 1.9813, 0.0953, 0.2975, 2.2042, 0.2407,
    2.9466, 0.5034, 0.6567,
)

DESIRED_RETENTION = 0.9
_DECAY = -0.5
# 0.9^(1/_DECAY) - 1 ~= 0.2345. With this factor, interval(S) == S at 90% recall.
_FACTOR = 0.9 ** (1 / _DECAY) - 1

MIN_STABILITY = 0.1
MAX_INTERVAL_DAYS = 365

# FSRS rating scale (distinct from the SM-2 0-5 quality): 1=Again 2=Hard 3=Good 4=Easy.
RATING_AGAIN, RATING_HARD, RATING_GOOD, RATING_EASY = 1, 2, 3, 4


def fsrs_rating_from_outcome(rating: str, recalled: Optional[bool]) -> int:
    """Map RetainHQ's two review signals onto an FSRS grade (1-4).

    A miss (recalled is False) is always Again — a lapse — regardless of how hard
    it felt. Otherwise the felt rating sets Hard/Good/Easy. A missing `recalled`
    (older clients) is treated as a successful recall, graded by feel.
    """
    if recalled is False:
        return RATING_AGAIN
    return {"hard": RATING_HARD, "medium": RATING_GOOD, "easy": RATING_EASY}.get(rating, RATING_GOOD)


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def _init_stability(rating: int) -> float:
    # S_0(g) = w_{g-1}, floored at MIN_STABILITY.
    return max(MIN_STABILITY, FSRS_WEIGHTS[rating - 1])


def _init_difficulty(rating: int) -> float:
    # D_0(g) = w4 - exp(w5*(g-1)) + 1, clamped to [1, 10].
    return _clamp(FSRS_WEIGHTS[4] - math.exp(FSRS_WEIGHTS[5] * (rating - 1)) + 1, 1.0, 10.0)


def _next_difficulty(difficulty: float, rating: int) -> float:
    # Linear nudge by grade, then mean-revert toward the Easy baseline.
    next_d = difficulty - FSRS_WEIGHTS[6] * (rating - 3)
    reverted = FSRS_WEIGHTS[7] * _init_difficulty(RATING_EASY) + (1 - FSRS_WEIGHTS[7]) * next_d
    return _clamp(reverted, 1.0, 10.0)


def _retrievability(elapsed_days: float, stability: float) -> float:
    # Predicted probability of recall after `elapsed_days` given current stability.
    return (1 + _FACTOR * elapsed_days / stability) ** _DECAY


def _next_stability(stability: float, difficulty: float, retrievability: float, rating: int) -> float:
    if rating == RATING_AGAIN:
        # Post-lapse stability: typically far lower, and never above pre-lapse S.
        s_fail = (
            FSRS_WEIGHTS[11]
            * difficulty ** (-FSRS_WEIGHTS[12])
            * ((stability + 1) ** FSRS_WEIGHTS[13] - 1)
            * math.exp(FSRS_WEIGHTS[14] * (1 - retrievability))
        )
        return max(MIN_STABILITY, min(s_fail, stability))
    hard_penalty = FSRS_WEIGHTS[15] if rating == RATING_HARD else 1.0
    easy_bonus = FSRS_WEIGHTS[16] if rating == RATING_EASY else 1.0
    growth = (
        math.exp(FSRS_WEIGHTS[8])
        * (11 - difficulty)
        * stability ** (-FSRS_WEIGHTS[9])
        * (math.exp(FSRS_WEIGHTS[10] * (1 - retrievability)) - 1)
        * hard_penalty
        * easy_bonus
    )
    return max(MIN_STABILITY, stability * (1 + growth))


def _interval_from_stability(stability: float) -> int:
    ivl = (stability / _FACTOR) * (DESIRED_RETENTION ** (1 / _DECAY) - 1)
    return int(_clamp(round(ivl), 1, MAX_INTERVAL_DAYS))


def apply_fsrs(activity: Activity, rating: int, now: Optional[datetime] = None) -> Review:
    """
    Advance the activity's FSRS memory state for a completed review of the given
    grade (1-4), then return the next due review. Mutates the activity in place;
    the caller adds the returned Review to the session.
    """
    now = now or datetime.utcnow()

    # NB: activity.difficulty_fsrs (FSRS 1-10) is distinct from activity.difficulty
    # (the user's 1-5 self-rating captured at log time) — do not conflate them.
    if activity.stability is None or activity.difficulty_fsrs is None:
        # First graded review of this card — establish state from the opening grade.
        stability = _init_stability(rating)
        difficulty = _init_difficulty(rating)
    else:
        if activity.last_reviewed_at is not None:
            elapsed = max(0.0, (now - activity.last_reviewed_at).total_seconds() / 86400.0)
        else:
            elapsed = float(activity.interval_days or 0)
        retrievability = _retrievability(elapsed, activity.stability)
        difficulty = _next_difficulty(activity.difficulty_fsrs, rating)
        stability = _next_stability(activity.stability, activity.difficulty_fsrs, retrievability, rating)

    interval = _interval_from_stability(stability)
    activity.stability = stability
    activity.difficulty_fsrs = difficulty
    activity.interval_days = interval
    # Legacy column kept roughly meaningful: reset on lapse, otherwise count up.
    activity.repetitions = 1 if rating == RATING_AGAIN else (activity.repetitions or 0) + 1
    activity.last_reviewed_at = now
    due_at = now + timedelta(days=interval)
    activity.next_review_at = due_at
    return Review(
        user_id=activity.user_id,
        activity_id=activity.id,
        status="due",
        scheduled_for=due_at,
    )
