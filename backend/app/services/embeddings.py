"""
Embedding service for vectorizing text.
Uses google.genai under the hood.
"""
import concurrent.futures
import math
from typing import Optional

from app.core.config import settings

# Belt: the SDK's own HTTP timeout. In practice a blackholed connection (no
# TCP reset, packets just dropped) doesn't reliably respect this — verified
# empirically, it still hung past this deadline. Suspenders: embed_batch
# below enforces a hard wall-clock bound with a real thread, independent of
# whether the SDK's transport cooperates.
_REQUEST_TIMEOUT_MS = 8_000
_EMBED_TIMEOUT_SEC = 8

# A blown deadline leaks the worker thread (there is no way to kill a thread
# stuck in a blocking socket call from the outside) — kept off the default
# executor and capped so a prolonged Gemini outage degrades to "embeddings
# unavailable" rather than exhausting the process's thread pool.
_executor = concurrent.futures.ThreadPoolExecutor(max_workers=4, thread_name_prefix="gemini-embed")


def _get_client():
    try:
        from google import genai
        from google.genai import types
    except ImportError as e:
        raise RuntimeError("The 'google-genai' package is not installed (pip install google-genai).") from e
    return genai.Client(
        api_key=settings.GEMINI_API_KEY,
        http_options=types.HttpOptions(timeout=_REQUEST_TIMEOUT_MS),
    )


def _embed_batch_call(clean_texts: list[str]) -> list[list[float]]:
    client = _get_client()
    try:
        response = client.models.embed_content(
            model=settings.EMBEDDING_MODEL,
            contents=clean_texts
        )
        return [list(emb.values) for emb in response.embeddings]
    except Exception as e:
        raise RuntimeError(f"Embedding call failed: {e}") from e


def embed_batch(texts: list[str]) -> list[list[float]]:
    """Get embedding vectors for a list of strings. Bounded to
    _EMBED_TIMEOUT_SEC wall-clock regardless of what the network does —
    callers can rely on this returning or raising within that window."""
    if not settings.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set.")

    clean_texts = [(t or "").strip() for t in texts]
    if not any(clean_texts):
        return [[] for _ in texts]

    future = _executor.submit(_embed_batch_call, clean_texts)
    try:
        return future.result(timeout=_EMBED_TIMEOUT_SEC)
    except concurrent.futures.TimeoutError:
        raise RuntimeError(f"Embedding call timed out after {_EMBED_TIMEOUT_SEC}s") from None

def embed(text: str) -> list[float]:
    """Get the embedding vector for a single string.
    Will raise an error if not configured or call fails."""
    return embed_batch([text])[0]


def similarity(a: list[float], b: list[float]) -> float:
    """Cosine similarity between two vectors."""
    if not a or not b:
        return 0.0
    dot_product = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(y * y for y in b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot_product / (mag_a * mag_b)
