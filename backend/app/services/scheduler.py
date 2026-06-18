from datetime import datetime, timedelta
from typing import Optional
from app.models.models import Activity, Review

# SM-2 spaced-repetition scheduling.
#
# Each Activity is one "card" carrying its own memory state (ease_factor,
# repetitions, interval_days). Logging an activity schedules the first review;
# completing a review computes the next interval and schedules the next one.
# Invariant: an activity in rotation has exactly one open status='due' review.

MIN_EASE_FACTOR = 1.3
DEFAULT_EASE_FACTOR = 2.5

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
    Initialize an activity's SM-2 state and return its first review.

    Default (immediate=False): the first review is scheduled for TOMORROW (+1 day).
    Quizzing a topic seconds after logging it measures short-term memory, not
    retention, and a batch of log-then-quiz prompts is the main source of review
    fatigue (log 4 topics -> 4 instant exams). The forgetting curve only starts
    to bite after a delay, so the first recall is worth far more a day later.
    Completing it advances the SM-2 ladder straight to +6d, then x ease.

    immediate=True: schedule the first review NOW. This is the one-time onboarding
    demo for a user's very FIRST activity — a brand-new user sees the recall loop
    instantly (our activation funnel leaks right after the first capture). It's a
    single demo card, not a per-log behavior, so it doesn't reintroduce fatigue.

    Every logged activity enters the rotation (no difficulty/hint gate).
    The activity must be flushed so it has an id before calling this.
    """
    now = now or datetime.utcnow()
    activity.ease_factor = DEFAULT_EASE_FACTOR
    if immediate:
        # Demo review due now. repetitions=0 so completing it still produces the
        # standard now -> +1d -> +6d ladder for this first card.
        activity.repetitions = 0
        activity.interval_days = 0
        due_at = now
    else:
        # repetitions=1 (not 0) treats the tomorrow review as the first banked
        # recall, so completing it jumps the ladder to +6d — the classic SM-2
        # 1->6 schedule — instead of an awkward +1d -> +1d. Mirrors the lapse reset.
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
    Map RetainHQ's two review signals onto an SM-2 quality grade (0-5).
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


def apply_sm2(activity: Activity, quality: int, now: Optional[datetime] = None) -> Review:
    """
    Advance the activity's SM-2 state for a completed review of the given
    quality, then return the next due review. Mutates activity in place; the
    caller is responsible for adding the returned Review to the session.
    """
    now = now or datetime.utcnow()

    if quality < 3:
        # Lapse: relearn from the start. We reset to repetitions=1 (not 0) on
        # purpose: the next successful recall then jumps straight to 6 days
        # (Fail -> +1d -> +6d). Resetting to 0 would give an awkward +1d -> +1d.
        activity.repetitions = 1
        activity.interval_days = 1
    else:
        # repetitions counts successful recalls. The first (tomorrow) review is
        # rep 1, so completing it lands on rep 2 (+6d), then interval x ease_factor.
        activity.repetitions += 1
        if activity.repetitions == 1:
            activity.interval_days = 1
        elif activity.repetitions == 2:
            activity.interval_days = 6
        else:  # rep 3+
            activity.interval_days = min(365, round(activity.interval_days * activity.ease_factor))

    # EF is updated on every completion (including lapses) and floored at 1.3.
    activity.ease_factor = max(
        MIN_EASE_FACTOR,
        activity.ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)),
    )

    due_at = now + timedelta(days=activity.interval_days)
    activity.last_reviewed_at = now
    activity.next_review_at = due_at
    return Review(
        user_id=activity.user_id,
        activity_id=activity.id,
        status="due",
        scheduled_for=due_at,
    )
