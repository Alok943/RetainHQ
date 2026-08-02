"""POST /api/companion/sessions — the browser extension's session sync.

Written 2026-08-02 to reproduce a live 500. This endpoint has existed since
Companion Phase 1 with ZERO test coverage, and — because the Firefox host
permission that lets the extension reach our API was never granted (D-054) —
it had also never received a single real request in production. The first
batch that ever arrived 500'd, and kept 500'ing until the retry cap dropped
the session.

The payload here mirrors exactly what `service_worker.ts`'s
`sessionToPayload` actually sends, not an idealized version.
"""
import uuid

import pytest
from httpx import AsyncClient
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.models import LearningEvent
from tests.conftest import USER_A


def _session(**over) -> dict:
    """Exactly the shape service_worker.ts builds."""
    base = {
        "session_id": str(uuid.uuid4()),
        "duration_min": 12,
        "occurred_at": "2026-08-02T10:00:00.000Z",
        "payload": {
            "sources": ["leetcode.com"],
            "title_sample": "Two Sum - LeetCode | Design Dynamic Array",
        },
    }
    base.update(over)
    return base


def test_rate_limit_window_is_naive_utc():
    """THE regression guard for the 500 this file was written to reproduce.

    Deliberately asserts on the helper's return value rather than going
    through the endpoint: the actual failure is asyncpg refusing to bind an
    aware datetime to a `timestamp without time zone` column, and SQLite —
    which this suite runs on — accepts that binding happily. An endpoint-level
    test therefore CANNOT catch this regression, and pretending otherwise
    would be worse than not testing it. Verified against real Postgres by
    hand: aware raises DataError, naive returns a count.
    """
    from app.api.routes.companion import utc_start_of_day

    start = utc_start_of_day()
    assert start.tzinfo is None, (
        "must be naive-UTC — asyncpg rejects an aware datetime against this "
        "schema's `timestamp without time zone` columns, 500ing every sync"
    )
    assert (start.hour, start.minute, start.second, start.microsecond) == (0, 0, 0, 0)


async def test_sync_a_plain_session_does_not_500(client: AsyncClient, db: AsyncSession):
    """The exact minimal case the extension sends for a non-LLM, non-YouTube
    surface — no content, no chapters, no node_id."""
    resp = await client.post("/api/companion/sessions", json={"sessions": [_session()]})
    assert resp.status_code == 200, resp.text

    body = resp.json()
    assert body["status"] == "ok"
    events = (await db.execute(
        select(LearningEvent).where(LearningEvent.user_id == uuid.UUID(USER_A.id))
    )).scalars().all()
    assert len(events) == 1
    assert events[0].event_type == "TIME_BLOCK"
    assert events[0].source == "companion_browser"
    assert events[0].trust_tier == "T3_observed"


async def test_sync_is_idempotent_on_resend(client: AsyncClient, db: AsyncSession):
    """The extension retries a failed batch up to 8 times; a batch that
    partially succeeded must not double-write on the retry."""
    s = _session()
    for _ in range(3):
        resp = await client.post("/api/companion/sessions", json={"sessions": [s]})
        assert resp.status_code == 200, resp.text

    events = (await db.execute(
        select(LearningEvent).where(LearningEvent.user_id == uuid.UUID(USER_A.id))
    )).scalars().all()
    assert len(events) == 1


async def test_sync_a_batch_of_several_sessions(client: AsyncClient, db: AsyncSession):
    """SEND_CHUNK_SIZE is 20 — a realistic backlog flush, not a single row."""
    sessions = [_session() for _ in range(5)]
    resp = await client.post("/api/companion/sessions", json={"sessions": sessions})
    assert resp.status_code == 200, resp.text

    events = (await db.execute(
        select(LearningEvent).where(LearningEvent.user_id == uuid.UUID(USER_A.id))
    )).scalars().all()
    assert len(events) == 5


async def test_sync_a_zero_duration_session(client: AsyncClient):
    """duration_min is `ge=0`, and the stitcher can legitimately produce 0 for
    a very short segment."""
    resp = await client.post(
        "/api/companion/sessions", json={"sessions": [_session(duration_min=0)]}
    )
    assert resp.status_code == 200, resp.text


async def test_sync_a_youtube_session_with_chapters(client: AsyncClient):
    """The chapter fan-out path — `chapters` rides as a transport-only sibling."""
    resp = await client.post("/api/companion/sessions", json={"sessions": [_session(
        payload={"sources": ["youtube.com"], "title_sample": "Graph Algorithms Full Course"},
        duration_min=30,
        chapters=[
            {"title": "Intro", "seconds": 300},
            {"title": "BFS", "seconds": 900},
            {"title": "DFS", "seconds": 600},
        ],
    )]})
    assert resp.status_code == 200, resp.text


async def test_client_cannot_forge_ai_attribution_fields(client: AsyncClient, db: AsyncSession):
    """Security invariant: confidence_band/classifier/reason etc. are stripped
    from client input — only the server's own classification may set them."""
    resp = await client.post("/api/companion/sessions", json={"sessions": [_session(
        payload={
            "sources": ["leetcode.com"],
            "title_sample": "Two Sum",
            "confidence_band": "high",
            "classifier": "totally-legit-model",
            "reason": "trust me",
        },
    )]})
    assert resp.status_code == 200, resp.text

    ev = (await db.execute(
        select(LearningEvent).where(LearningEvent.user_id == uuid.UUID(USER_A.id))
    )).scalars().first()
    assert ev.payload.get("classifier") != "totally-legit-model"
    assert ev.payload.get("reason") != "trust me"
