"""One-off backfill: replay the owner's already-completed, node-linked reviews
through the evidence spine (SPEC-career-coach-phase1.md).

Producer A (app/api/routes/reviews.py's complete_review hook) only emits a
learning_event on FUTURE review completions — there's no path for reviews
that were already completed before this feature existed. The spec's exit
criterion ("a mastery number for the owner's real RetainHQ history that the
owner reads and agrees with") needs that history in learning_events first.

Idempotent: uses the same entity_id=review.id dedupe key as the live hook, so
re-running this (or a later real completion of the same review, which can't
happen — reviews don't re-open) never double-counts.

Run:
    ./.venv/Scripts/python.exe backfill_evidence.py <user_id>
"""
import asyncio
import sys
import uuid

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import async_session_maker
from app.models.models import Activity, Review
from app.services import evidence, metrics


async def main(user_id: uuid.UUID) -> None:
    async with async_session_maker() as db:
        reviews = (
            await db.execute(
                select(Review)
                .options(selectinload(Review.activity))
                .where(Review.user_id == user_id, Review.status == "completed")
                .order_by(Review.completed_at.asc())
            )
        ).scalars().all()

        written = skipped_unmapped = skipped_ungraded = 0
        for review in reviews:
            activity: Activity = review.activity
            if activity.node_id is None:
                skipped_unmapped += 1
                # Same metric Producer A emits live (§6.3) — so GET /summary's
                # unmapped_events reflects the full history, not just what
                # happens to complete from today onward.
                await metrics.record_metric_event(
                    db, user_id,
                    event_type="evidence_unmapped",
                    payload={"reason": "no_node_id", "activity_id": str(activity.id), "backfill": True},
                )
                await db.commit()
                continue

            grade = evidence.recall_grade(review.recalled, review.rating, review.quality)
            if grade is None:
                skipped_ungraded += 1
                continue

            event = await evidence.record_event(
                db, user_id,
                event_type="RECALL_GRADED",
                trust_tier="T2_verified_internal",
                source="retainhq_review",
                node_id=activity.node_id,
                grade=grade,
                outcome="pass" if review.recalled else "fail",
                duration_min=round(review.duration_ms / 60000) if review.duration_ms else 0,
                entity_id=review.id,
                occurred_at=review.completed_at,
                payload={
                    "rating": review.rating,
                    "recalled": review.recalled,
                    "quality": review.quality,
                    "ai_verdict": review.ai_verdict,
                    "backfill": True,
                },
            )
            if event is not None:
                written += 1
            await db.commit()

        nodes_recomputed = await evidence.recompute_user(db, user_id)
        await db.commit()

        print(f"Reviews scanned:        {len(reviews)}")
        print(f"Events written:         {written}")
        print(f"Skipped (no node_id):   {skipped_unmapped}")
        print(f"Skipped (no grade):     {skipped_ungraded}")
        print(f"Nodes recomputed:       {nodes_recomputed}")


if __name__ == "__main__":
    asyncio.run(main(uuid.UUID(sys.argv[1])))
