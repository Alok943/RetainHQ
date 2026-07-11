"""
Syllabus → roadmap extraction: one model call turning an uploaded syllabus PDF
into a DRAFT roadmap (units → atomic topics).

Provider-routed by settings.SYLLABUS_MODEL: a "gemini*" id calls Google
(GEMINI_API_KEY), anything else calls Anthropic (ANTHROPIC_API_KEY). Both paths
send the SAME system prompt + JSON schema and return a raw JSON string that the
shared code below validates and caps — so swapping providers to compare
extraction quality is just a config change.

Design constraints:
  - The output is a PROPOSAL, never written to the DB here. The user reviews and
    edits the draft in the UI, then commits it via a separate endpoint — an LLM
    syllabus parse is ~90% right and the 10% must be user-correctable before save.
  - Node granularity is the whole game: a syllabus line like "Electromagnetic
    Induction" is a chapter, not a recallable card. The prompt forces decomposition
    into atomic, testable topics so logged activities (and their FSRS cards) stay
    sharp instead of mushy.
  - The PDF goes to the model as a document/inline part (vision path) — no
    client-side text extraction, so scanned/table-heavy syllabi work too.
  - Structured output guarantees schema-valid JSON; Pydantic re-validates and
    applies size caps as defense in depth.
"""
import base64

from pydantic import BaseModel, Field, ValidationError

from app.core.config import settings


def _uses_gemini() -> bool:
    return settings.SYLLABUS_MODEL.lower().startswith("gemini")


def extraction_configured() -> bool:
    """True when the selected provider has a key — drives the route's 404 gate."""
    return bool(settings.GEMINI_API_KEY) if _uses_gemini() else bool(settings.ANTHROPIC_API_KEY)


class SyllabusError(RuntimeError):
    pass


class DraftTopic(BaseModel):
    title: str
    description: str = ""


class DraftUnit(BaseModel):
    title: str
    topics: list[DraftTopic] = Field(default_factory=list)


class SyllabusDraft(BaseModel):
    title: str
    description: str = ""
    units: list[DraftUnit] = Field(default_factory=list)


# Hand-written (not model_json_schema()) so we control the constraint surface:
# structured outputs require additionalProperties:false + required on every object.
_DRAFT_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string", "description": "Short roadmap title, e.g. 'Operating Systems — Sem 5'"},
        "description": {"type": "string", "description": "One-line summary of what this syllabus covers"},
        "units": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Unit/module/chapter name as in the syllabus"},
                    "topics": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title": {"type": "string", "description": "One atomic, testable topic"},
                                "description": {"type": "string", "description": "One line: what to be able to recall"},
                            },
                            "required": ["title", "description"],
                            "additionalProperties": False,
                        },
                    },
                },
                "required": ["title", "topics"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["title", "description", "units"],
    "additionalProperties": False,
}

_SYSTEM_PROMPT = (
    "You convert an academic syllabus PDF into a learning roadmap for a spaced-repetition app. "
    "The user will log study activity against each topic and be quizzed on it later, so every "
    "topic must be an ATOMIC, TESTABLE unit of knowledge — something a learner can recall in "
    "one sitting — not a chapter heading.\n"
    "Rules:\n"
    "1. Preserve the syllabus's own structure as units (modules/chapters/sections), in the "
    "syllabus's order.\n"
    "2. DECOMPOSE each syllabus line into atomic topics. 'Electromagnetic Induction' is a "
    "chapter — split it into topics like 'State Faraday's law of induction' or 'Apply Lenz's "
    "law to find induced current direction'. Aim for 3-10 topics per syllabus line depending "
    "on its breadth; a genuinely narrow line can stay as one topic.\n"
    "3. Phrase each topic title as a capability where natural ('Define…', 'Derive…', 'Apply…', "
    "'Compare…'), under ~80 characters.\n"
    "4. Each topic's description is ONE line stating what the learner should be able to recall.\n"
    "5. Cover the WHOLE syllabus — do not drop units. Ignore non-content pages (grading "
    "policy, textbook lists, administrative details).\n"
    "6. If the document is not a syllabus/curriculum at all, return a single unit titled "
    "'Not a syllabus' with zero topics."
)


_USER_PROMPT = "Convert this syllabus into a roadmap."


async def _extract_anthropic(pdf_bytes: bytes) -> str:
    """Anthropic (Claude) path. Returns the raw JSON string."""
    try:
        from anthropic import AsyncAnthropic
    except ImportError as e:
        raise SyllabusError("The 'anthropic' package is not installed (pip install anthropic).") from e

    client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    try:
        # Streaming: extraction of a dense syllabus can run past HTTP timeouts
        # non-streamed; we only need the final message.
        async with client.messages.stream(
            model=settings.SYLLABUS_MODEL,
            max_tokens=32000,
            thinking={"type": "adaptive"},
            system=_SYSTEM_PROMPT,
            output_config={"format": {"type": "json_schema", "schema": _DRAFT_SCHEMA}},
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "document",
                            "source": {
                                "type": "base64",
                                "media_type": "application/pdf",
                                "data": base64.standard_b64encode(pdf_bytes).decode("ascii"),
                            },
                        },
                        {"type": "text", "text": _USER_PROMPT},
                    ],
                }
            ],
        ) as stream:
            message = await stream.get_final_message()
    except Exception as e:  # network / API / rate-limit — surface as one error class
        raise SyllabusError(f"Syllabus extraction call failed: {e}") from e
    finally:
        await client.close()

    if message.stop_reason == "refusal":
        raise SyllabusError("The model declined to process this document.")
    if message.stop_reason == "max_tokens":
        raise SyllabusError("This syllabus is too dense to extract in one pass — try a shorter PDF.")

    return next((b.text for b in message.content if b.type == "text"), "")


async def _extract_gemini(pdf_bytes: bytes) -> str:
    """Google (Gemini) path. Returns the raw JSON string.

    Uses the same JSON schema as the Anthropic path via response_schema +
    response_mime_type='application/json'. The PDF is an inline document part
    (Gemini's native PDF understanding), so scanned/table syllabi work here too.
    """
    try:
        from google import genai
        from google.genai import types
    except ImportError as e:
        raise SyllabusError("The 'google-genai' package is not installed (pip install google-genai).") from e

    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    try:
        resp = await client.aio.models.generate_content(
            model=settings.SYLLABUS_MODEL,
            contents=[
                types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf"),
                _USER_PROMPT,
            ],
            config=types.GenerateContentConfig(
                system_instruction=_SYSTEM_PROMPT,
                response_mime_type="application/json",
                response_schema=_DRAFT_SCHEMA,
                max_output_tokens=32000,
            ),
        )
    except Exception as e:  # network / API / rate-limit — surface as one error class
        raise SyllabusError(f"Syllabus extraction call failed: {e}") from e

    # A safety/recitation block or an output-token cutoff comes back as no usable
    # text — surface it as our own error rather than an opaque .text AttributeError.
    text = getattr(resp, "text", None)
    if not text:
        raise SyllabusError("The model returned no usable output for this document.")
    return text


async def extract_roadmap_from_pdf(pdf_bytes: bytes) -> SyllabusDraft:
    """One model call: syllabus PDF in, validated draft roadmap out. Provider is
    routed by settings.SYLLABUS_MODEL (Gemini vs Anthropic).

    Raises SyllabusError when the feature is unconfigured, the API call fails,
    or the response can't be validated.
    """
    if not extraction_configured():
        key = "GEMINI_API_KEY" if _uses_gemini() else "ANTHROPIC_API_KEY"
        raise SyllabusError(f"{key} is not set — syllabus extraction is disabled.")

    raw = await (_extract_gemini(pdf_bytes) if _uses_gemini() else _extract_anthropic(pdf_bytes))

    try:
        draft = SyllabusDraft.model_validate_json(raw)
    except ValidationError as e:
        raise SyllabusError(f"Extraction returned malformed JSON: {e}") from e

    # Defense-in-depth caps so a pathological parse can't flood the review UI or DB.
    draft.units = [u for u in draft.units if u.title.strip()][:40]
    for unit in draft.units:
        unit.title = unit.title.strip()[:200]
        unit.topics = [t for t in unit.topics if t.title.strip()][:60]
        for t in unit.topics:
            t.title = t.title.strip()[:200]
            t.description = t.description.strip()[:500]
    draft.title = draft.title.strip()[:200] or "Uploaded syllabus"
    draft.description = draft.description.strip()[:500]

    if not any(u.topics for u in draft.units):
        raise SyllabusError(
            "Couldn't find syllabus content in this PDF — make sure it's a course syllabus or curriculum."
        )
    return draft
