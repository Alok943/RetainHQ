import asyncio
import uuid
from typing import Optional, Literal
from pydantic import BaseModel
from google import genai
from google.genai import types

from app.core.config import settings

# Companion classification always runs on Flash-Lite (fast, cheap).
COMPANION_CLASSIFIER_MODEL = "gemini-2.0-flash-lite"
COMPANION_PROMPT_VERSION = "v1"

# Without this, the SDK's HTTP client has no timeout — a stalled connection
# would hang the whole session-sync request (see embeddings.py's same fix).
_REQUEST_TIMEOUT_MS = 8_000

class CandidateRank(BaseModel):
    node: str
    rank: int

class ClassificationResult(BaseModel):
    candidates: list[CandidateRank]
    selected: Optional[str]
    confidence_band: Literal["high", "medium", "low"]
    study_type: str
    assistance_level: Optional[Literal["none", "hint", "llm_assisted", "solution_seen"]]
    reason: str

async def classify_session(
    title_sample: str,
    sources: list[str],
    candidates: list[dict],
    memory: list[str] = None,
    *,
    consent_tier: Optional[str] = None,
    content: Optional[str] = None,
) -> ClassificationResult:
    """
    Rung 3 of the Classification Ladder.
    Uses Gemini Flash-Lite to evaluate the top-K candidate nodes from the embedding search,
    and returns a structured JSON response assigning the session to a node (or dropping it).

    `content`/`consent_tier` (IMPLEMENTATION-companion-consent.md §4.3): no producer
    sets `content` today — `title_sample` is metadata (a page title), not chat
    content, and metadata classification needs no consent at all
    (SPEC-companion-phase1.md §6). This guard exists for the phase-6 feature
    that WILL add a real content-bearing field, written now while the
    invariant (no content field exists yet) is still true and cheap to keep.
    """
    if content is not None and consent_tier != "cloud":
        raise ValueError("content-bearing classification requires the 'cloud' consent tier")

    if not settings.GEMINI_API_KEY:
        # Fallback to triage if no LLM configured
        return ClassificationResult(
            candidates=[],
            selected=None,
            confidence_band="medium",
            study_type="unknown",
            assistance_level=None,
            reason="LLM not configured"
        )
        
    client = genai.Client(
        api_key=settings.GEMINI_API_KEY,
        http_options=types.HttpOptions(timeout=_REQUEST_TIMEOUT_MS),
    )
    
    # Format candidates for the prompt
    candidates_text = ""
    valid_uuids = set()
    for i, c in enumerate(candidates):
        candidates_text += f"[{i+1}] Node ID: {c['node_id']}\nTitle: {c['title']}\nDescription: {c.get('description', '')}\n\n"
        valid_uuids.add(str(c["node_id"]))
        
    prompt = f"""
You are a career coaching AI. Your job is to classify a user's web browser study session and map it to exactly ONE of their predefined career roadmap nodes, IF it matches.

# Session Data
Sources: {", ".join(sources)}
Title/Metadata: {title_sample}
Recent topics (memory): {", ".join(memory) if memory else "None"}

# Candidate Nodes (Top {len(candidates)} Matches)
{candidates_text}

# Task
Evaluate the session metadata against the candidate nodes.
1. Does this session clearly map to one of the candidates?
2. What type of studying was this? (e.g. video_lecture, practice_problem, reading)
3. Did the user receive assistance? (For LLM chats, assume "llm_assisted". For LeetCode solutions, "solution_seen".)

Return ONLY JSON matching the requested schema.
- `candidates`: list of nodes you considered, with your ranking (1 is best).
- `selected`: the Node ID of the best match. MUST BE EXACTLY ONE OF THE PROVIDED NODE IDs. If no node matches well, set to null.
- `confidence_band`: 
   - "high" if you are certain this maps directly to the selected node.
   - "medium" if it might match, but requires human triage.
   - "low" if this is unrelated to any candidate and unrelated to career development.
- `study_type`: a short string categorizing the activity.
- `assistance_level`: "none", "hint", "llm_assisted", or "solution_seen". (Default to "llm_assisted" if it's a ChatGPT/Claude/Gemini source unless obvious otherwise).
- `reason`: a 1-sentence explanation of your choice.
"""

    try:
        # .aio is real async I/O (unlike embeddings.embed_batch's sync SDK
        # call), so wait_for's cancellation actually reaches the underlying
        # connection — this bounds the request instead of merely hoping the
        # SDK's own http_options.timeout is honored end-to-end.
        response = await asyncio.wait_for(
            client.aio.models.generate_content(
                model=COMPANION_CLASSIFIER_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=ClassificationResult,
                    temperature=0.0
                ),
            ),
            timeout=_REQUEST_TIMEOUT_MS / 1000,
        )

        result = response.parsed

        # Validation: Never invent a node
        if result.selected and result.selected not in valid_uuids:
            hallucinated = result.selected
            result.selected = None
            result.confidence_band = "medium"
            result.reason = f"System override: LLM hallucinated node {hallucinated}"

        return result
        
    except Exception as e:
        # Failsafe: drop to triage
        return ClassificationResult(
            candidates=[],
            selected=None,
            confidence_band="medium",
            study_type="unknown",
            assistance_level=None,
            reason=f"LLM Classification failed: {str(e)}"
        )
