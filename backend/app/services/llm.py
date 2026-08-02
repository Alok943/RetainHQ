"""One provider-routed JSON call, for every model id in `config.py`.

Why this exists
---------------
Provider dispatch used to be re-implemented per service, each with its own rules
and its own error type: `career_tree.py` routed `gemini*`/`claude*`/OpenAI-compat
by string prefix, `syllabus.py` did its own `gemini*` check, `grader.py` was
hardwired to Groq and additionally branched on `openai/gpt-oss` to decide whether
`reasoning_effort` was a legal parameter. Changing which model serves a feature
meant knowing which of those three dialects the feature spoke.

The rule here: **a model id is a setting in `config.py`, and the provider is
derived from the id.** Nothing outside this module should test a model id's
prefix, and no model id should be written as a literal anywhere but `config.py`.

Routing (by the id, never by a separate provider flag — one source of truth):

    gemini*   → Google (`GEMINI_API_KEY`), native `response_schema`
    anything  → Groq   (`GROQ_API_KEY`), `response_format={"type":"json_object"}`

`syllabus.py` and `career_tree.py` still carry their own copies: they need
inline-PDF parts and a 32k output cap respectively, and both are live features
whose regression cost is higher than the tidiness gain. Folding them in is a
separate, testable change — see BACKLOG.
"""
import asyncio
from typing import Optional, Type

from pydantic import BaseModel

from app.core.config import settings

# Bound every call. An un-timeouted SDK client can hang a whole request; the
# grader sits inline in the review path, where latency is existential for an SRS.
_REQUEST_TIMEOUT_S = 30.0


class LLMError(RuntimeError):
    """Any failure to obtain a usable response: unconfigured, network, or malformed."""


def provider_for(model: str) -> str:
    return "gemini" if model.lower().startswith("gemini") else "groq"


def is_configured(model: str) -> bool:
    """Whether the key this model needs is present. Callers use this to stay
    gated-off cleanly rather than raising into a user-facing path."""
    return bool(settings.GEMINI_API_KEY if provider_for(model) == "gemini" else settings.GROQ_API_KEY)


async def _call_gemini(
    model: str, system_prompt: str, user_msg: str, max_tokens: int, schema: Optional[Type[BaseModel]]
) -> str:
    try:
        from google import genai
        from google.genai import types
    except ImportError as e:
        raise LLMError("The 'google-genai' package is not installed (pip install google-genai).") from e

    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    config = {
        "system_instruction": system_prompt,
        "response_mime_type": "application/json",
        "max_output_tokens": max_tokens,
        "temperature": 0,
    }
    # Native structured output when the caller has a model for the response.
    # Stronger than Groq's json_object mode, which only promises *some* valid JSON.
    if schema is not None:
        config["response_schema"] = schema

    resp = await asyncio.wait_for(
        client.aio.models.generate_content(
            model=model,
            contents=[user_msg],
            config=types.GenerateContentConfig(**config),
        ),
        timeout=_REQUEST_TIMEOUT_S,
    )
    out = getattr(resp, "text", None)
    if not out:
        raise LLMError("The model returned no usable output.")
    return out


async def _call_groq(
    model: str, system_prompt: str, user_msg: str, max_tokens: int, reasoning: str
) -> str:
    try:
        from groq import AsyncGroq
    except ImportError as e:
        raise LLMError("The 'groq' package is not installed (pip install groq).") from e

    # gpt-oss is a reasoning model whose hidden reasoning tokens count against
    # max_tokens. The flag is gpt-oss-only — sending it to a llama model 400s —
    # so it is gated on the id here rather than at any call site.
    extra = {}
    if model.startswith("openai/gpt-oss"):
        extra["reasoning_effort"] = reasoning

    client = AsyncGroq(api_key=settings.GROQ_API_KEY)
    resp = await asyncio.wait_for(
        client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_msg},
            ],
            response_format={"type": "json_object"},
            temperature=0,
            max_tokens=max_tokens,
            **extra,
        ),
        timeout=_REQUEST_TIMEOUT_S,
    )
    return resp.choices[0].message.content


async def call_json(
    *,
    model: str,
    system_prompt: str,
    user_msg: str,
    max_tokens: int = 700,
    reasoning: str = "low",
    schema: Optional[Type[BaseModel]] = None,
) -> str:
    """Return the model's raw JSON string. Raises LLMError on any failure.

    `reasoning` is honoured only where the provider exposes it as a parameter
    (currently gpt-oss on Groq). Gemini models do their own thinking-budget
    management, so on that branch it is a documented no-op rather than a
    silently-dropped argument — callers should not assume it is being applied.
    """
    if not is_configured(model):
        key = "GEMINI_API_KEY" if provider_for(model) == "gemini" else "GROQ_API_KEY"
        raise LLMError(f"{key} is not set — this feature is disabled.")

    try:
        if provider_for(model) == "gemini":
            return await _call_gemini(model, system_prompt, user_msg, max_tokens, schema)
        return await _call_groq(model, system_prompt, user_msg, max_tokens, reasoning)
    except LLMError:
        raise
    except asyncio.TimeoutError as e:
        raise LLMError(f"Model call timed out after {_REQUEST_TIMEOUT_S}s ({model}).") from e
    except Exception as e:  # network / API / rate-limit / quota
        raise LLMError(f"Model call failed ({model}): {e}") from e
