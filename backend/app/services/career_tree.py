"""
Career tree generation: one model call that ADAPTS a versioned role template
for one learner (SPEC-career-coach-phase2.md §3). Copies services/syllabus.py's
shape almost exactly — provider routing, hand-written JSON schema for strict
structured output, Pydantic re-validation as defense in depth.

Design constraints (parent design doc §6, enforced here):
  - The model ADAPTS a template, it does not invent a syllabus from scratch.
    The template is always in the prompt as ground truth.
  - The output is a PROPOSAL — this module never touches the DB. The route
    layer (api/routes/career.py) handles review + commit.
  - A model that violates a hard rule (invented subject, >90 nodes, a cycle,
    a non-'custom.'-prefixed new stable_key) gets exactly one retry with the
    violation named in the prompt, then falls back to the UNMODIFIED
    template. Never fail onboarding with an error screen — a generic tree
    the user edits beats that.

Templates ship from backend/app/data/career_templates/ (a synced copy — see
sync_career_templates.py's docstring for why content/career-templates/, the
canonical authoring + CI-validated location, can't be read directly at
runtime: Render's backend service deploys with root=backend/, so the sibling
content/ directory is outside the Docker build context).
"""
import json
import logging
import re
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field, ValidationError

from app.core.config import settings

logger = logging.getLogger(__name__)

TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "data" / "career_templates"
_ROLE_TEMPLATE_RE = re.compile(r"^([a-z][a-z0-9_]*)\.v(\d+)\.json$")

# §3.3 hard rules enforced after every model call.
MAX_NODES = 90
MAX_NEW_NODES = 10
NEW_NODE_PREFIX = "custom."


class CareerTreeError(RuntimeError):
    pass


class DraftCareerNode(BaseModel):
    stable_key: str
    title: str
    est_effort_min: int = Field(gt=0)
    priority: int = Field(ge=1, le=5)
    depends_on: list[str] = Field(default_factory=list)
    diagnostic_probe: Optional[str] = None
    # Grading rubric for diagnostic_probe (grader.grade_recall's key_memory) —
    # never shown to the model as something to invent; carried through from
    # the template only (see _template_to_draft / diagnostic.py).
    diagnostic_answer: Optional[str] = None


class DraftCareerSubject(BaseModel):
    key: str
    title: str
    default_priority: int = Field(ge=1, le=5)
    nodes: list[DraftCareerNode] = Field(default_factory=list)


class CareerTreeDraft(BaseModel):
    role_key: str
    template_version: str
    title: str
    subjects: list[DraftCareerSubject] = Field(default_factory=list)


# --- Templates ---------------------------------------------------------------

def list_templates() -> list[dict]:
    """Every role's LATEST version on disk — role_key, title, version, node_count."""
    best: dict[str, tuple[int, Path]] = {}
    for path in TEMPLATES_DIR.glob("*.json"):
        m = _ROLE_TEMPLATE_RE.match(path.name)
        if not m:
            continue
        role_key, version_num = m.group(1), int(m.group(2))
        if role_key not in best or version_num > best[role_key][0]:
            best[role_key] = (version_num, path)

    out = []
    for role_key, (_version_num, path) in sorted(best.items()):
        data = json.loads(path.read_text(encoding="utf-8"))
        node_count = sum(len(s.get("nodes", [])) for s in data.get("subjects", []))
        out.append({
            "role_key": role_key,
            "title": data.get("title", role_key),
            "version": data.get("version"),
            "node_count": node_count,
        })
    return out


def _load_template(role_key: str) -> dict:
    templates = {t["role_key"]: t for t in list_templates()}
    if role_key not in templates:
        raise CareerTreeError(f"Unknown role_key '{role_key}'.")
    version = templates[role_key]["version"]
    path = TEMPLATES_DIR / f"{role_key}.{version}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _template_to_draft(role_key: str, template: dict) -> CareerTreeDraft:
    return CareerTreeDraft(
        role_key=role_key,
        template_version=template["version"],
        title=template["title"],
        subjects=[
            DraftCareerSubject(
                key=s["key"],
                title=s["title"],
                default_priority=s["default_priority"],
                nodes=[
                    DraftCareerNode(
                        stable_key=n["stable_key"],
                        title=n["title"],
                        est_effort_min=n["est_effort_min"],
                        priority=n["priority"],
                        depends_on=list(n.get("depends_on") or []),
                        diagnostic_probe=n.get("diagnostic_probe"),
                        diagnostic_answer=n.get("diagnostic_answer"),
                    )
                    for n in s.get("nodes", [])
                ],
            )
            for s in template.get("subjects", [])
        ],
    )


# --- Validation (§3.3 "the model may not...") --------------------------------

def _find_cycle(graph: dict) -> Optional[list]:
    """DFS cycle detection over stable_key -> [depends_on stable_keys]."""
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {k: WHITE for k in graph}
    path = []

    def visit(node):
        color[node] = GRAY
        path.append(node)
        for dep in graph.get(node, ()):
            if dep not in color:
                continue
            if color[dep] == GRAY:
                return path[path.index(dep):] + [dep]
            if color[dep] == WHITE:
                cycle = visit(dep)
                if cycle:
                    return cycle
        path.pop()
        color[node] = BLACK
        return None

    for node in graph:
        if color[node] == WHITE:
            cycle = visit(node)
            if cycle:
                return cycle
    return None


def _validate_draft(draft: CareerTreeDraft, template: dict) -> list[str]:
    """Returns a list of violation messages — empty means the draft is clean."""
    violations = []
    template_subject_keys = {s["key"] for s in template.get("subjects", [])}
    template_stable_keys = {n["stable_key"] for s in template.get("subjects", []) for n in s.get("nodes", [])}

    invented_subjects = {s.key for s in draft.subjects} - template_subject_keys
    if invented_subjects:
        violations.append(f"invented new subject key(s) {sorted(invented_subjects)} — subjects must come from the template")

    all_nodes = [n for s in draft.subjects for n in s.nodes]
    if len(all_nodes) > MAX_NODES:
        violations.append(f"{len(all_nodes)} nodes exceeds the {MAX_NODES}-node limit")

    new_nodes = [n for n in all_nodes if n.stable_key not in template_stable_keys]
    if len(new_nodes) > MAX_NEW_NODES:
        violations.append(f"{len(new_nodes)} new nodes exceeds the {MAX_NEW_NODES}-new-node limit")

    stable_keys_seen = set()
    graph = {}
    for node in all_nodes:
        if node.stable_key in stable_keys_seen:
            violations.append(f"duplicate stable_key '{node.stable_key}'")
        stable_keys_seen.add(node.stable_key)
        graph[node.stable_key] = list(node.depends_on)
        if node.stable_key not in template_stable_keys and not node.stable_key.startswith(NEW_NODE_PREFIX):
            violations.append(f"new node '{node.stable_key}' must use the '{NEW_NODE_PREFIX}<slug>' stable_key prefix")

    for stable_key, deps in graph.items():
        for dep in deps:
            if dep not in stable_keys_seen:
                violations.append(f"'{stable_key}' depends_on unresolved stable_key '{dep}'")

    cycle = _find_cycle(graph)
    if cycle:
        violations.append(f"dependency cycle: {' -> '.join(cycle)}")

    return violations


def _restore_diagnostic_fields(draft: CareerTreeDraft, template: dict) -> None:
    """diagnostic_probe/diagnostic_answer are authored, stable content (§4:
    "Not generated fresh — probes are authored content, so they're reviewable
    and stable") — never trust the model to reproduce them verbatim, since a
    paraphrased rubric could silently drift from the authored ground truth.
    Overwrite from the template by stable_key on every generation, in place.
    New ('custom.'-prefixed) nodes have no template entry, so they get none —
    consistent with the diagnostic only ever drawing from template nodes."""
    template_probes = {
        n["stable_key"]: (n.get("diagnostic_probe"), n.get("diagnostic_answer"))
        for s in template.get("subjects", []) for n in s.get("nodes", [])
    }
    for subject in draft.subjects:
        for node in subject.nodes:
            probe, answer = template_probes.get(node.stable_key, (None, None))
            node.diagnostic_probe = probe
            node.diagnostic_answer = answer


# --- Model call ---------------------------------------------------------------

def _provider() -> str:
    """Route by model id: 'gemini*' -> Google, 'claude*' -> Anthropic, anything
    else -> an OpenAI-compatible endpoint.

    The previous rule was "gemini* -> Google, EVERYTHING else -> Anthropic",
    which silently sent a DeepSeek/Qwen/GLM id to Anthropic and failed on an
    unknown-model error that named the wrong vendor. Being explicit about all
    three keeps a cost-driven provider switch to an env change.
    """
    model = settings.CAREER_TREE_MODEL.lower()
    if model.startswith("gemini"):
        return "gemini"
    if model.startswith("claude"):
        return "anthropic"
    return "openai_compat"


def generation_configured() -> bool:
    provider = _provider()
    if provider == "gemini":
        return bool(settings.GEMINI_API_KEY)
    if provider == "anthropic":
        return bool(settings.ANTHROPIC_API_KEY)
    return bool(settings.OPENAI_COMPAT_BASE_URL and settings.OPENAI_COMPAT_API_KEY)


def _uses_gemini() -> bool:
    """Kept for callers/tests that predate the three-way router."""
    return _provider() == "gemini"


_SYSTEM_PROMPT = (
    "You adapt a career-role learning tree template for one specific learner. "
    "You are ADAPTING, not inventing: the template is the source of truth for scope and structure.\n"
    "Rules — you MUST follow every one:\n"
    "1. You may drop nodes the learner has demonstrably already mastered (per their diagnostic results or free-text context).\n"
    f"2. You may add AT MOST {MAX_NEW_NODES} new nodes for gaps the template misses. Every new node's stable_key MUST start with '{NEW_NODE_PREFIX}' (e.g. '{NEW_NODE_PREFIX}graphql_basics').\n"
    "3. You may adjust each node's priority (1-5) and reorder nodes within a subject.\n"
    "4. You may rewrite node titles for clarity.\n"
    "5. You must NEVER invent a new top-level subject key — every subject.key in your output must be one of the template's own subject keys.\n"
    "6. You must NEVER create a dependency cycle, and every depends_on must resolve to a stable_key present in your own output.\n"
    f"7. Your output must have NO MORE than {MAX_NODES} nodes total.\n"
    "8. Every stable_key you emit that isn't new must be copied EXACTLY from the template — never invent a variant of an existing key.\n"
    "Return the full tree in the same role_key/template_version/title/subjects/nodes shape as the template, including every field."
)

_DRAFT_SCHEMA = {
    "type": "object",
    "properties": {
        "role_key": {"type": "string"},
        "template_version": {"type": "string"},
        "title": {"type": "string"},
        "subjects": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "key": {"type": "string"},
                    "title": {"type": "string"},
                    "default_priority": {"type": "integer"},
                    "nodes": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "stable_key": {"type": "string"},
                                "title": {"type": "string"},
                                "est_effort_min": {"type": "integer"},
                                "priority": {"type": "integer"},
                                "depends_on": {"type": "array", "items": {"type": "string"}},
                                "diagnostic_probe": {"type": ["string", "null"]},
                            },
                            "required": ["stable_key", "title", "est_effort_min", "priority", "depends_on", "diagnostic_probe"],
                            "additionalProperties": False,
                        },
                    },
                },
                "required": ["key", "title", "default_priority", "nodes"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["role_key", "template_version", "title", "subjects"],
    "additionalProperties": False,
}


def _build_prompt(
    template: dict, goal_title: str, target_date, diagnostic_results: Optional[list], free_text: Optional[str],
) -> str:
    parts = [
        f"TEMPLATE:\n{json.dumps(template, indent=2)}",
        f"\nGOAL: {goal_title}" + (f" (target date: {target_date})" if target_date else " (open-ended)"),
    ]
    if diagnostic_results:
        parts.append(f"\nDIAGNOSTIC RESULTS: {json.dumps(diagnostic_results, indent=2)}")
    if free_text:
        parts.append(f"\nLEARNER CONTEXT: {free_text.strip()[:2000]}")
    parts.append("\nAdapt this template for this learner. Return the adapted tree.")
    return "\n".join(parts)


async def _call_anthropic(prompt: str) -> str:
    try:
        from anthropic import AsyncAnthropic
    except ImportError as e:
        raise CareerTreeError("The 'anthropic' package is not installed (pip install anthropic).") from e

    client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    try:
        async with client.messages.stream(
            model=settings.CAREER_TREE_MODEL,
            max_tokens=32000,
            thinking={"type": "adaptive"},
            system=_SYSTEM_PROMPT,
            output_config={"format": {"type": "json_schema", "schema": _DRAFT_SCHEMA}},
            messages=[{"role": "user", "content": prompt}],
        ) as stream:
            message = await stream.get_final_message()
    except Exception as e:
        raise CareerTreeError(f"Career tree generation call failed: {e}") from e
    finally:
        await client.close()

    if message.stop_reason == "refusal":
        raise CareerTreeError("The model declined to generate a tree.")
    if message.stop_reason == "max_tokens":
        raise CareerTreeError("The tree was too large to generate in one pass.")
    return next((b.text for b in message.content if b.type == "text"), "")


async def _call_gemini(prompt: str) -> str:
    try:
        from google import genai
        from google.genai import types
    except ImportError as e:
        raise CareerTreeError("The 'google-genai' package is not installed (pip install google-genai).") from e

    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    try:
        resp = await client.aio.models.generate_content(
            model=settings.CAREER_TREE_MODEL,
            contents=[prompt],
            config=types.GenerateContentConfig(
                system_instruction=_SYSTEM_PROMPT,
                response_mime_type="application/json",
                response_schema=CareerTreeDraft,
                max_output_tokens=32000,
            ),
        )
    except Exception as e:
        raise CareerTreeError(f"Career tree generation call failed: {e}") from e

    out = getattr(resp, "text", None)
    if not out:
        raise CareerTreeError("The model returned no usable output.")
    return out


# The lowercase word "json" in here is LOAD-BEARING, not styling. DeepSeek's and
# Qwen/DashScope's JSON modes both require the literal token "json" to appear in
# the messages; DashScope validates it server-side and returns 400 without it.
# The serialized schema below cannot be relied on to supply it (Pydantic emits
# "properties"/"type"/"$defs", not necessarily "json"), and an uppercase-only
# "JSON" is not worth betting a 400 on. Verified 2026-07-26 against both vendors'
# docs — see DECISIONS D-044.
_JSON_ONLY_INSTRUCTION = (
    "\n\nRespond with json only: a single json object matching this schema, "
    "with no prose and no markdown fences.\n"
)


async def _call_openai_compatible(prompt: str) -> str:
    """Any OpenAI-compatible /chat/completions endpoint (DeepSeek, Qwen, Moonshot,
    Zhipu, Together, local vLLM).

    Spoken over httpx rather than the `openai` SDK: this is one unstreamed JSON
    POST, and the wire protocol is what's portable, not the client library.

    Structured output is `response_format={"type":"json_object"}` — JSON mode, NOT
    strict `json_schema`. Strict nested-schema support varies sharply across these
    providers and several accept the parameter while ignoring the constraints,
    which fails *silently* and is worse than not asking. So the schema is put in
    the prompt and correctness is enforced downstream by _validate_draft + the
    retry. That is a genuinely weaker guarantee than Gemini's native
    response_schema — the instrumentation in generate_career_tree exists so the
    difference is measurable rather than assumed.
    """
    import httpx

    schema = json.dumps(CareerTreeDraft.model_json_schema())
    body = {
        "model": settings.CAREER_TREE_MODEL,
        "messages": [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {
                "role": "user",
                "content": prompt + _JSON_ONLY_INSTRUCTION + schema,
            },
        ],
        "response_format": {"type": "json_object"},
        "max_tokens": settings.OPENAI_COMPAT_MAX_TOKENS,
    }
    url = settings.OPENAI_COMPAT_BASE_URL.rstrip("/") + "/chat/completions"
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                url,
                json=body,
                headers={"Authorization": f"Bearer {settings.OPENAI_COMPAT_API_KEY}"},
            )
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        raise CareerTreeError(f"Career tree generation call failed: {e}") from e

    try:
        out = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as e:
        raise CareerTreeError(f"Unexpected response shape from {url}: {str(data)[:200]}") from e
    if not out:
        raise CareerTreeError("The model returned no usable output.")
    return out


async def _call_model(prompt: str) -> str:
    """The one seam tests monkeypatch — dispatches to whichever provider
    CAREER_TREE_MODEL routes to. Never called if generation_configured() is False."""
    provider = _provider()
    if provider == "gemini":
        return await _call_gemini(prompt)
    if provider == "anthropic":
        return await _call_anthropic(prompt)
    return await _call_openai_compatible(prompt)


def _report(on_outcome, outcome: str, role_key: str, violations: list) -> None:
    """Hand the generation outcome to the caller (the route records a
    metric_event). Optional and failure-isolated: observability must never be
    able to break generation itself."""
    if on_outcome is None:
        return
    try:
        on_outcome(outcome, role_key, violations)
    except Exception:
        logger.exception("career-tree outcome reporter failed (ignored)")


async def generate_career_tree(
    role_key: str,
    goal_title: str,
    target_date=None,
    diagnostic_results: Optional[list[dict]] = None,
    free_text: Optional[str] = None,
    on_outcome=None,
) -> CareerTreeDraft:
    """Draft tree: template + goal + diagnostic + free text -> validated,
    adapted tree. NEVER touches the DB. NEVER raises for onboarding — an
    unconfigured provider, a call failure, or two straight validation
    failures all fall back to the unmodified template.
    """
    template = _load_template(role_key)

    if not generation_configured():
        _report(on_outcome, 'fallback_unconfigured', role_key, [])
        return _template_to_draft(role_key, template)

    prompt = _build_prompt(template, goal_title, target_date, diagnostic_results, free_text)

    for attempt in range(2):  # one attempt + one retry
        violations: list[str]
        try:
            raw = await _call_model(prompt)
            draft = CareerTreeDraft.model_validate_json(raw)
        except (ValidationError, CareerTreeError) as e:
            violations = [str(e)]
        else:
            _restore_diagnostic_fields(draft, template)
            violations = _validate_draft(draft, template)
            if not violations:
                _report(
                    on_outcome,
                    "adapted" if attempt == 0 else "adapted_after_retry",
                    role_key, [],
                )
                return draft

        logger.warning(
            "Career tree attempt %d/2 rejected for %s (%s): %s",
            attempt + 1, role_key, settings.CAREER_TREE_MODEL, "; ".join(violations)[:500],
        )
        if attempt == 0:
            prompt = prompt + (
                f"\n\nYour previous attempt was REJECTED for: {'; '.join(violations)}. "
                "Fix this and return a corrected tree."
            )

    # Both attempts failed. The user still gets a usable tree — but it is the
    # UNMODIFIED template, identical for every learner of this role, and until
    # this was instrumented that was indistinguishable from a good adaptation:
    # the endpoint returned 200 with a valid tree and nothing was logged. A model
    # that is misconfigured, deprecated, or simply bad at nested JSON degrades
    # every user to the generic template in total silence. Never let that be
    # quiet again — this is the signal that makes a provider swap measurable.
    logger.error(
        "Career tree FELL BACK to the unmodified template for %s (model=%s) — "
        "every learner of this role gets an identical tree until this is fixed. Last violations: %s",
        role_key, settings.CAREER_TREE_MODEL, "; ".join(violations)[:500],
    )
    _report(on_outcome, "fallback_validation", role_key, violations)
    return _template_to_draft(role_key, template)
