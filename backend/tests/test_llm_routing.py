"""The model-id → provider rule, and the invariant that keeps it usable.

The point of `services/llm.py` is that switching a feature between providers is
a one-line change in `config.py`. That only stays true if (a) routing really is
derived from the id and (b) nobody reintroduces a model literal in a service
file. Both are asserted here — (b) is the one that rots silently.
"""
import pathlib
import re

import pytest

from app.core.config import Settings, settings
from app.services import llm


@pytest.mark.parametrize("model,expected", [
    ("gemini-3.5-flash-lite", "gemini"),
    ("gemini-3.6-flash", "gemini"),
    ("Gemini-3.5-Flash-Lite", "gemini"),   # case-insensitive
    ("openai/gpt-oss-120b", "groq"),
    ("llama-3.3-70b-versatile", "groq"),
])
def test_provider_is_derived_from_the_id(model, expected):
    assert llm.provider_for(model) == expected


def test_is_configured_checks_the_right_key(monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "x")
    monkeypatch.setattr(settings, "GROQ_API_KEY", "")
    assert llm.is_configured("gemini-3.5-flash-lite") is True
    assert llm.is_configured("openai/gpt-oss-120b") is False


def test_grader_follows_grader_model(monkeypatch):
    """Flipping GRADER_MODEL must move the grader between providers with no
    other change — this is the whole claim D-058 rests on."""
    from app.services import grader

    monkeypatch.setattr(settings, "GEMINI_API_KEY", "")
    monkeypatch.setattr(settings, "GROQ_API_KEY", "x")

    monkeypatch.setattr(settings, "GRADER_MODEL", "gemini-3.5-flash-lite")
    assert grader.is_configured() is False       # no Gemini key
    monkeypatch.setattr(settings, "GRADER_MODEL", "openai/gpt-oss-120b")
    assert grader.is_configured() is True        # Groq key present


# Every model id lives in config.py. `llm.py` may name provider PREFIXES (that
# is its job); nothing else may name a model.
# Matches a real model ID, not the family name. `"gemini-embed"` (a thread-name
# prefix) and `"gemini-embedding"` (a telemetry label) are descriptions of which
# model produced something, not ids passed to an SDK — those are fine.
_MODEL_LITERAL = re.compile(
    r'"(gemini-\d|gemini-embedding-\d|claude-[a-z]|openai/gpt-|llama-\d|text-embedding-\d)'
)
_ALLOWED = {"config.py", "llm.py"}


def test_no_model_ids_are_hardcoded_outside_config():
    app_dir = pathlib.Path(__file__).resolve().parents[1] / "app"
    offenders = []
    for path in app_dir.rglob("*.py"):
        if path.name in _ALLOWED:
            continue
        for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if line.lstrip().startswith("#"):
                continue
            if _MODEL_LITERAL.search(line):
                offenders.append(f"{path.relative_to(app_dir)}:{i}: {line.strip()}")
    assert not offenders, (
        "Model ids must be settings in core/config.py, not literals in service files:\n"
        + "\n".join(offenders)
    )


def test_every_model_setting_routes_to_a_known_provider():
    for name, value in Settings().model_dump().items():
        if name.endswith("_MODEL") and isinstance(value, str) and value:
            assert llm.provider_for(value) in {"gemini", "groq"}, f"{name}={value}"
