#!/usr/bin/env python3
"""Caveman validator for RetainHQ content JSON. Pure stdlib — no installs.

Run from the repo root:  python content/validate.py
Checks every roadmaps/<roadmap>/<slug>.json for:
  - required fields + correct types/enums
  - slug matches filename
  - sources present and look like URLs
  - prerequisites/unlocks resolve to other curated slugs in the SAME roadmap
Exits non-zero if anything fails, so it can gate a commit later.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent / "roadmaps"
SLUG = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")

KIND = {"concept", "milestone"}
TIER = {"tier1", "tier2", "tier3"}
DIFF = {"easy", "medium", "hard"}
FREQ = {"low", "medium", "high"}
CHECK_TYPES = {"predict-output", "predict-result", "explain-behavior", "find-bug", "choose-model", "debug-misconception"}
RUNTIMES = {"python", "sql"}

errors = []
warnings = []


def err(f, msg):
    errors.append(f"  [FAIL] {f}: {msg}")


def warn(f, msg):
    warnings.append(f"  [warn] {f}: {msg}")


def req(d, key, f, typ=None):
    if key not in d:
        err(f, f"missing required field '{key}'")
        return False
    if typ is not None and not isinstance(d[key], typ):
        err(f, f"'{key}' should be {typ.__name__}, got {type(d[key]).__name__}")
        return False
    return True


def main():
    if not ROOT.exists():
        print(f"No content yet at {ROOT}. Curate a topic first.")
        return 0

    files = sorted(ROOT.glob("*/*.json"))
    if not files:
        print("No topic JSON found under content/roadmaps/<roadmap>/.")
        return 0

    # First pass: load + per-file checks, build slug index per roadmap.
    by_roadmap = {}
    docs = {}
    for path in files:
        rel = path.relative_to(ROOT.parent)
        try:
            d = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            err(rel, f"invalid JSON: {e}")
            continue
        docs[path] = d

        for k in ("slug", "title", "roadmap", "kind", "tier"):
            req(d, k, rel, str)
        if d.get("slug") and not SLUG.match(d["slug"]):
            err(rel, f"slug '{d['slug']}' is not kebab-case")
        if d.get("slug") and d["slug"] != path.stem:
            err(rel, f"slug '{d['slug']}' != filename '{path.stem}'")
        if d.get("kind") not in KIND:
            err(rel, f"kind must be one of {KIND}")
        if d.get("tier") not in TIER:
            err(rel, f"tier must be one of {TIER}")
        if d.get("roadmap") and d["roadmap"] != path.parent.name:
            err(rel, f"roadmap '{d['roadmap']}' != folder '{path.parent.name}'")

        m = d.get("metadata")
        if not isinstance(m, dict):
            err(rel, "missing 'metadata' object")
        else:
            if m.get("difficulty") not in DIFF:
                err(rel, f"metadata.difficulty must be one of {DIFF}")
            if m.get("interview_frequency") not in FREQ:
                err(rel, f"metadata.interview_frequency must be one of {FREQ}")
            if not isinstance(m.get("importance"), int) or not (1 <= m.get("importance", 0) <= 10):
                err(rel, "metadata.importance must be int 1-10")
            for edge in ("prerequisites", "unlocks"):
                if not isinstance(m.get(edge), list):
                    err(rel, f"metadata.{edge} must be a list of slugs")

        ov = d.get("overview")
        if not isinstance(ov, dict) or not all(ov.get(k) for k in ("what", "why")):
            err(rel, "overview.what and overview.why are required")

        for k in ("why_learning_this", "common_mistakes", "recall_questions", "practice_tasks", "sources"):
            if not isinstance(d.get(k), list) or not d.get(k):
                err(rel, f"'{k}' must be a non-empty list")

        for i, s in enumerate(d.get("sources", []) or []):
            if not isinstance(s, str) or not s.startswith("http"):
                err(rel, f"sources[{i}] is not a URL: {s!r}")

        for i, rq in enumerate(d.get("recall_questions", []) or []):
            if not isinstance(rq, dict) or not rq.get("q") or not rq.get("answer"):
                err(rel, f"recall_questions[{i}] needs both 'q' and 'answer'")

        # Execution block branches on runtime: python -> code_walkthrough, sql -> query_walkthrough.
        runtime = d.get("runtime", "python")
        if runtime not in RUNTIMES:
            err(rel, f"runtime must be one of {RUNTIMES}")
        if runtime == "sql":
            qw = d.get("query_walkthrough")
            if not isinstance(qw, dict) or not qw.get("query"):
                err(rel, "query_walkthrough is required for runtime 'sql': an object with a non-empty 'query'")
            if d.get("code_walkthrough") is not None:
                err(rel, "code_walkthrough not allowed for runtime 'sql' — use query_walkthrough")
        else:
            cw = d.get("code_walkthrough")
            if not isinstance(cw, dict) or not cw.get("code"):
                err(rel, "code_walkthrough is required: an object with a non-empty 'code' string")
            elif not cw.get("focus"):
                err(rel, "code_walkthrough.focus is required (the one state change to watch)")

        # challenge is OPTIONAL (Tier D) — but if present it must be well-formed.
        ch = d.get("challenge")
        if ch is not None and (not isinstance(ch, dict) or not all(ch.get(k) for k in ("title", "prompt"))):
            err(rel, "challenge, if present, needs non-empty 'title' and 'prompt'")

        # understanding_checks (Tier A) — REQUIRED: >=2 typed mental-model probes.
        uc = d.get("understanding_checks")
        if not isinstance(uc, list) or len(uc) < 2:
            err(rel, "understanding_checks is required: a list of >=2 mental-model probes")
        else:
            for i, c in enumerate(uc):
                if not isinstance(c, dict) or not all(c.get(k) for k in ("type", "question", "answer", "why")):
                    err(rel, f"understanding_checks[{i}] needs non-empty 'type', 'question', 'answer', and 'why'")
                elif c.get("type") not in CHECK_TYPES:
                    err(rel, f"understanding_checks[{i}].type must be one of {CHECK_TYPES}")

        am = d.get("aha_moment")
        if am is not None and (
            not isinstance(am, dict)
            or not all(am.get(k) for k in ("code", "prediction", "common_guess", "why"))
        ):
            err(rel, "aha_moment must have non-empty code, prediction, common_guess, and why")

        if d.get("roadmap"):
            by_roadmap.setdefault(d["roadmap"], set()).add(d.get("slug"))

    # Second pass: cross-reference prereq/unlock slugs within the same roadmap.
    for path, d in docs.items():
        rel = path.relative_to(ROOT.parent)
        known = by_roadmap.get(d.get("roadmap"), set())
        m = d.get("metadata") or {}
        for edge in ("prerequisites", "unlocks"):
            for slug in m.get(edge, []) or []:
                if slug not in known:
                    warn(rel, f"{edge} '{slug}' not curated yet in this roadmap")

    print(f"Checked {len(files)} topic file(s).\n")
    if warnings:
        print("Warnings (unresolved refs - fine while curating):")
        print("\n".join(warnings), "\n")
    if errors:
        print("Errors:")
        print("\n".join(errors))
        print(f"\n{len(errors)} error(s). Fix or re-prompt Gemini.")
        return 1
    print("All content valid. [OK]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
