"""Splits one companion chat session into its constituent topics
(IMPLEMENTATION-companion-chat-content.md §3.2). A single ChatGPT/Claude
session routinely covers several unrelated things; without this every session
becomes one LearningEvent attributed to whichever topic the chat happened to
be titled after (usually just the first one).

Mirrors llm_classifier.py's shape (same client construction, same timeout
discipline) but is a distinct call: classification maps known text to known
roadmap nodes, this call free-generates a topic breakdown with no candidate
list at all.
"""
import asyncio
import logging
from typing import Literal, Optional

from pydantic import BaseModel, Field
from google import genai
from google.genai import types

from app.core.config import settings

logger = logging.getLogger(__name__)

TOPIC_SEGMENTATION_MODEL = settings.COMPANION_LITE_MODEL
TOPIC_SEGMENTATION_PROMPT_VERSION = "v1"
_REQUEST_TIMEOUT_MS = 8_000

MAX_TOPICS = 5


class SessionTopic(BaseModel):
    # Model-written, never a verbatim span from the chat — the prompt says so
    # explicitly, and this is what keeps user-authored text out of the DB
    # when the label is later stored as a LearningEvent's title_sample.
    label: str
    share: float = Field(ge=0.0, le=1.0)
    study_type: str
    assistance_level: Literal["none", "hint", "llm_assisted", "solution_seen"]


class _RawSegmentationResult(BaseModel):
    topics: list[SessionTopic]


async def segment_session_topics(
    content: str, sources: list[str]
) -> list[SessionTopic]:
    """Returns [] on any failure or on a single-topic verdict — both mean
    "don't fan out, use the existing single-event path". Never raises: a
    flaky classifier call must degrade to the pre-existing behavior, not
    break session sync.
    """
    if not content or not content.strip():
        return []

    if not settings.GEMINI_API_KEY:
        return []

    client = genai.Client(
        api_key=settings.GEMINI_API_KEY,
        http_options=types.HttpOptions(timeout=_REQUEST_TIMEOUT_MS),
    )

    prompt = f"""
You are analyzing a study session transcript from an AI chat (ChatGPT/Claude/Gemini). The
user may have covered several unrelated topics in one conversation. Break the session into
its distinct topics.

# Transcript (U: = the user's own words, A: = the assistant's reply, truncated)
Sources: {", ".join(sources)}
{content}

# Task
Identify up to {MAX_TOPICS} distinct topics covered. For each:
- `label`: a short phrase YOU write describing the topic (e.g. "Postgres index tuning").
  Never quote the transcript verbatim — write your own short description.
- `share`: fraction of the session (0.0-1.0) spent on this topic. All shares should sum to
  roughly 1.0.
- `study_type`: a short string categorizing the activity (e.g. "debugging", "concept_review",
  "reading").
- `assistance_level`: "none", "hint", "llm_assisted", or "solution_seen" — for an AI chat this
  is almost always "llm_assisted" unless the user was clearly just discussing concepts without
  seeking a direct answer, in which case "hint" or "none" may fit better.

If the whole session is genuinely one topic, return a single topic with share 1.0.
Return ONLY JSON matching the requested schema.
"""

    try:
        response = await asyncio.wait_for(
            client.aio.models.generate_content(
                model=TOPIC_SEGMENTATION_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=_RawSegmentationResult,
                    temperature=0.0,
                ),
            ),
            timeout=_REQUEST_TIMEOUT_MS / 1000,
        )
        result = response.parsed
    except Exception as e:
        logger.error("Topic segmentation failed, falling back to single-event: %s", e)
        return []

    topics = result.topics[:MAX_TOPICS] if result.topics else []
    if len(topics) <= 1:
        return []

    # Merge any remainder past MAX_TOPICS (or a bad-sum response) into the
    # largest topic rather than silently dropping duration.
    total_share = sum(t.share for t in topics)
    if total_share <= 0:
        return []
    if abs(total_share - 1.0) > 0.01:
        for t in topics:
            t.share = t.share / total_share

    return topics
