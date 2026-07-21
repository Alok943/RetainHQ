"""
Embedding service for vectorizing text.
Uses google.genai under the hood.
"""
import math
from typing import Optional

from app.core.config import settings

def _get_client():
    try:
        from google import genai
    except ImportError as e:
        raise RuntimeError("The 'google-genai' package is not installed (pip install google-genai).") from e
    return genai.Client(api_key=settings.GEMINI_API_KEY)


def embed_batch(texts: list[str]) -> list[list[float]]:
    """Get embedding vectors for a list of strings."""
    if not settings.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set.")
    
    clean_texts = [(t or "").strip() for t in texts]
    if not any(clean_texts):
        return [[] for _ in texts]
        
    client = _get_client()
    try:
        response = client.models.embed_content(
            model="gemini-embedding-001",
            contents=clean_texts
        )
        return [list(emb.values) for emb in response.embeddings]
    except Exception as e:
        raise RuntimeError(f"Embedding call failed: {e}") from e

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
