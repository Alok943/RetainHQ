"""Every source_type the Log Activity form offers must be accepted by the API.

`self_learn` shipped in frontend/src/LogActivity.jsx's SOURCE_TYPES but was never
added to VALID_SOURCES, so choosing "Self Learning (sites / LLMs / RetainHQ)" and
submitting returned 422 and silently lost the capture. The two lists are one
contract split across two files; this test is the thing that holds them together.
"""
import re
from pathlib import Path

import pytest

from app.schemas.activity import VALID_SOURCES
from tests.conftest import USER_A  # noqa: F401  (imported for the auth fixture chain)

LOG_ACTIVITY_JSX = Path(__file__).parent.parent.parent / "frontend" / "src" / "LogActivity.jsx"

BASE_PAYLOAD = {
    "topic": "Binary search",
    "difficulty": 3,
    "needed_hint": False,
    "key_memory": "Halve the search space each step; O(log n).",
}


def _frontend_source_values() -> list[str]:
    """Parse SOURCE_TYPES out of the JSX rather than duplicating it here — a
    hardcoded copy would drift the same way the original bug did."""
    text = LOG_ACTIVITY_JSX.read_text(encoding="utf-8")
    block = re.search(r"const SOURCE_TYPES = \[(.*?)\];", text, re.S)
    assert block, "SOURCE_TYPES not found in LogActivity.jsx — did the form change shape?"
    return re.findall(r"value:\s*'([^']+)'", block.group(1))


def test_every_frontend_source_type_is_valid_server_side():
    if not LOG_ACTIVITY_JSX.exists():
        pytest.skip("frontend not present in this checkout")
    allowed = set(VALID_SOURCES.__args__)
    offered = _frontend_source_values()
    assert offered, "parsed zero source types — the regex is stale"
    missing = [v for v in offered if v not in allowed]
    assert not missing, (
        f"LogActivity.jsx offers source types the API rejects with 422: {missing}. "
        "Add them to VALID_SOURCES in app/schemas/activity.py."
    )


@pytest.mark.parametrize("source_type", ["problem", "self_learn", "lesson", "other"])
async def test_activity_accepts_source_type(client, source_type):
    resp = await client.post(
        "/api/activities/", json={**BASE_PAYLOAD, "source_type": source_type}
    )
    assert resp.status_code == 200, resp.text


async def test_unknown_source_type_is_still_rejected(client):
    """The Literal is a real allow-list, not decoration."""
    resp = await client.post(
        "/api/activities/", json={**BASE_PAYLOAD, "source_type": "telepathy"}
    )
    assert resp.status_code == 422
