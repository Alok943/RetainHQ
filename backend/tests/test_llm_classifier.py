"""services/llm_classifier.classify_session's content-gate
(IMPLEMENTATION-companion-consent.md §4.3). No producer sets `content` yet —
title_sample is metadata, not chat content, so this guard is scaffolding for
the phase-6 feature that will add a real content-bearing field. Written now,
tested now, so the enforcement point can't be skipped later by accident.
"""
import pytest

from app.services.llm_classifier import classify_session


async def test_content_without_cloud_tier_is_rejected():
    with pytest.raises(ValueError, match="cloud"):
        await classify_session(
            "some title", ["claude.ai"], [], content="raw chat text", consent_tier="titles",
        )


async def test_content_with_no_tier_at_all_is_rejected():
    with pytest.raises(ValueError, match="cloud"):
        await classify_session("some title", ["claude.ai"], [], content="raw chat text", consent_tier=None)


async def test_content_with_cloud_tier_passes_the_gate(monkeypatch):
    """Doesn't assert anything about the (unconfigured-in-tests) Gemini call
    itself — only that the gate doesn't raise before reaching it."""
    from app.core.config import settings
    monkeypatch.setattr(settings, "GEMINI_API_KEY", None)
    result = await classify_session(
        "some title", ["claude.ai"], [], content="raw chat text", consent_tier="cloud",
    )
    assert result.reason == "LLM not configured"


async def test_no_content_field_needs_no_tier_at_all():
    """Today's actual call shape — title_sample-only metadata classification
    — must keep working with no consent_tier supplied at all."""
    result = await classify_session("some title", ["leetcode.com"], [])
    assert result is not None
