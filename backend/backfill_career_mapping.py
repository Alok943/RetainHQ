"""One-shot backfill: map the owner's previously-unmapped activities against
their newly committed career tree (SPEC-career-coach-phase2.md §5).

Phase 1 counted unmapped evidence (activities.node_id IS NULL, tracked via
`evidence_unmapped` MetricEvents) but had nothing to map onto. Now that a
career tree exists (POST /api/career/tree/commit), this re-runs
topic_mapping.suggest_node over every activity phase 1 flagged and is still
unmapped:

  - Tier 2 >= AUTO_MAP_THRESHOLD (high confidence): written directly. This
    script is a one-shot admin batch over the owner's OWN history, not a live
    user-facing flow — unlike the interactive /unmapped/{id}/assign endpoint,
    there's no live-editing-mistake risk to guard against by always requiring
    a click, so "auto-maps" (§5) means what it says here.
  - Tier 2 in the triage band, or no match at all: left alone. The owner
    triages those via GET/POST /api/career/unmapped in the app.

Concrete fix for phase 1's §6.3 finding — and because phase 1 made mastery a
pure fold over events (Design law 2), this backfill is a script, not a
migration: it only ever calls record_event + recompute_user, the same paths
every other producer uses.

Idempotent: backfill_activity's writes ride record_event's existing
entity_id dedupe (review.id), so re-running this is safe — already-mapped
activities are skipped (node_id is no longer NULL) and no event double-counts.

Run:
    ./.venv/Scripts/python.exe backfill_career_mapping.py <user_id>
"""
import asyncio
import sys
import uuid

from sqlalchemy import select

from app.core.database import async_session_maker
from app.models.models import Activity, MetricEvent
from app.services import evidence, topic_mapping


async def _unmapped_activity_ids(db, user_id: uuid.UUID) -> set:
    """Every activity_id phase 1's Producer A ever flagged evidence_unmapped
    for this user — the concrete backlog this script spends (§6.3)."""
    payloads = (
        await db.execute(
            select(MetricEvent.payload).where(
                MetricEvent.user_id == user_id, MetricEvent.event_type == "evidence_unmapped",
            )
        )
    ).scalars().all()
    ids = set()
    for payload in payloads:
        raw = (payload or {}).get("activity_id")
        if raw:
            ids.add(uuid.UUID(raw))
    return ids


async def main(user_id: uuid.UUID) -> None:
    async with async_session_maker() as db:
        candidates = await topic_mapping.candidate_nodes_for_active_goal(db, user_id)
        if not candidates:
            print("No committed career tree for this user (no active goal, or goal.roadmap_id is NULL) — nothing to map against.")
            return

        flagged_ids = await _unmapped_activity_ids(db, user_id)
        activities = []
        if flagged_ids:
            activities = (
                await db.execute(
                    select(Activity).where(
                        Activity.user_id == user_id,
                        Activity.node_id.is_(None),
                        Activity.id.in_(flagged_ids),
                    )
                )
            ).scalars().all()

        before = len(activities)
        auto_mapped = triaged = no_match = events_written = 0

        for activity in activities:
            suggestion = topic_mapping.suggest_node(activity.topic, candidates)
            if suggestion is None:
                no_match += 1
                continue
            if suggestion["tier"] != "auto":
                triaged += 1
                continue
            written = await topic_mapping.backfill_activity(db, user_id, activity.id, suggestion["node_id"])
            await db.commit()
            events_written += written
            auto_mapped += 1

        nodes_recomputed = await evidence.recompute_user(db, user_id)
        await db.commit()

        print(f"Unmapped activities before:                  {before}")
        print(f"Auto-mapped (>= {topic_mapping.AUTO_MAP_THRESHOLD:.2f} confidence):        {auto_mapped}")
        print(f"Left for triage ({topic_mapping.TRIAGE_THRESHOLD:.2f}-{topic_mapping.AUTO_MAP_THRESHOLD:.2f} confidence):   {triaged}")
        print(f"No match (< {topic_mapping.TRIAGE_THRESHOLD:.2f} confidence):             {no_match}")
        print(f"learning_events written:                     {events_written}")
        print(f"Still unmapped/in-triage after (share):       {triaged + no_match} ({(triaged + no_match) / before:.0%})" if before else "Still unmapped/in-triage after:               0")
        print(f"Nodes recomputed:                             {nodes_recomputed}")


if __name__ == "__main__":
    asyncio.run(main(uuid.UUID(sys.argv[1])))
