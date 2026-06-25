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

KIND = {"concept", "milestone", "aptitude", "reasoning", "theory"}
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

        # Aptitude is its OWN thin lesson shape (kind: "aptitude"): intuition + rule + trick + recall.
        # None of the python/sql fields (overview, *_walkthrough, understanding_checks, practice_tasks)
        # apply — branch entirely and skip them. See content/PROMPT-aptitude.md.
        if d.get("kind") == "aptitude":
            mm = d.get("mental_model")
            if not isinstance(mm, dict) or not mm.get("intuition"):
                err(rel, "mental_model is required (object with a non-empty 'intuition' one-liner)")
            fm = d.get("formula")
            if not isinstance(fm, dict) or not fm.get("statement"):
                err(rel, "formula is required (object with a non-empty 'statement')")
            sc = d.get("shortcuts")
            if not isinstance(sc, list) or not sc:
                err(rel, "shortcuts is required: a non-empty list of trick cards")
            else:
                for i, s in enumerate(sc):
                    if not isinstance(s, dict) or not s.get("title") or not s.get("trick"):
                        err(rel, f"shortcuts[{i}] needs non-empty 'title' and 'trick'")
            cm = d.get("common_mistakes")
            if not isinstance(cm, list) or not cm:
                err(rel, "common_mistakes is required: a non-empty list")
            else:
                for i, c in enumerate(cm):
                    if not isinstance(c, dict) or not c.get("title") or not c.get("explanation"):
                        err(rel, f"common_mistakes[{i}] needs non-empty 'title' and 'explanation'")
            rq = d.get("recall_questions")
            if not isinstance(rq, list) or len(rq) < 3:
                err(rel, "recall_questions is required: >=3 items")
            else:
                for i, q in enumerate(rq):
                    if not isinstance(q, dict) or not q.get("q") or not q.get("answer"):
                        err(rel, f"recall_questions[{i}] needs both 'q' and 'answer'")
            oq = d.get("oa_questions")
            if not isinstance(oq, list) or len(oq) < 2:
                err(rel, "oa_questions is required: >=2 OA-style items")
            else:
                for i, q in enumerate(oq):
                    if not isinstance(q, dict) or not q.get("question") or not q.get("answer"):
                        err(rel, f"oa_questions[{i}] needs both 'question' and 'answer'")
            # hook + pattern_discovery are OPTIONAL; validate shape if present, enforce THE LAW.
            hk = d.get("hook")
            if hk is not None and (not isinstance(hk, dict) or not hk.get("scenario")):
                err(rel, "hook, if present, needs a non-empty 'scenario'")
            pd = d.get("pattern_discovery")
            if pd is not None:
                cases = pd.get("cases") if isinstance(pd, dict) else None
                if not isinstance(pd, dict) or not isinstance(cases, list) or not cases or not pd.get("rule"):
                    err(rel, "pattern_discovery, if present, needs a non-empty 'cases' list and a 'rule'")
                elif not all(isinstance(c, str) and c.strip() for c in cases):
                    err(rel, "pattern_discovery.cases must be a list of non-empty observation STRINGS (not objects)")
                else:
                    keys = list(d.keys())
                    if "formula" in keys and keys.index("pattern_discovery") > keys.index("formula"):
                        warn(rel, "THE LAW: pattern_discovery should come BEFORE formula (discovery first)")
            srcs = d.get("sources")
            if not isinstance(srcs, list) or not srcs:
                err(rel, "'sources' must be a non-empty list")
            else:
                for i, s in enumerate(srcs):
                    if not isinstance(s, str) or not s.startswith("http"):
                        err(rel, f"sources[{i}] is not a URL: {s!r}")
            if d.get("roadmap"):
                by_roadmap.setdefault(d["roadmap"], set()).add(d.get("slug"))
            continue

        # Theory (Core CS: OS/DBMS/Networks, System Design) is a no-runtime concept
        # lesson (kind: "theory"): intuition + an EXPLANATION + recall. No code/formula/method.
        # See content/PROMPT-coreCS.md.
        if d.get("kind") == "theory":
            mm = d.get("mental_model")
            if not isinstance(mm, dict) or not mm.get("intuition"):
                err(rel, "mental_model is required (object with a non-empty 'intuition')")
            if not isinstance(d.get("explanation"), str) or not d.get("explanation").strip():
                err(rel, "explanation is required: a non-empty string (the concept, plainly explained)")
            kp = d.get("key_points")
            if kp is not None:
                if not isinstance(kp, list) or not all(isinstance(p, dict) and p.get("title") and p.get("detail") for p in kp):
                    err(rel, "key_points, if present, must be a list of {title, detail} objects")
            # animation (optional, PROCESS concepts only): actors + directed steps so a
            # generic SVG renderer can animate the process. `term` per step is optional.
            an = d.get("animation")
            if an is not None:
                if not isinstance(an, dict) or an.get("type") not in {"sequence", "cycle", "timeline"}:
                    err(rel, "animation.type must be one of sequence|cycle|timeline")
                else:
                    actors = an.get("actors")
                    ids = {a.get("id") for a in actors} if isinstance(actors, list) else set()
                    if not isinstance(actors, list) or len(actors) < 2 or not all(isinstance(a, dict) and a.get("id") and a.get("label") for a in actors):
                        err(rel, "animation.actors must be a list of >=2 {id, label}")
                    steps = an.get("steps")
                    if not isinstance(steps, list) or not steps or not all(
                        isinstance(s, dict) and s.get("from") in ids and s.get("to") in ids and s.get("label") for s in steps
                    ):
                        err(rel, "animation.steps must be a non-empty list of {from, to, label} referencing actor ids")
            cm = d.get("common_mistakes")
            if not isinstance(cm, list) or not cm:
                err(rel, "common_mistakes is required: a non-empty list")
            else:
                for i, c in enumerate(cm):
                    if not isinstance(c, dict) or not c.get("title") or not c.get("explanation"):
                        err(rel, f"common_mistakes[{i}] needs non-empty 'title' and 'explanation'")
            rq = d.get("recall_questions")
            if not isinstance(rq, list) or len(rq) < 3:
                err(rel, "recall_questions is required: >=3 items")
            else:
                for i, q in enumerate(rq):
                    if not isinstance(q, dict) or not q.get("q") or not q.get("answer"):
                        err(rel, f"recall_questions[{i}] needs both 'q' and 'answer'")
            oq = d.get("oa_questions")
            if not isinstance(oq, list) or len(oq) < 2:
                err(rel, "oa_questions is required: >=2 interview-style items")
            else:
                for i, q in enumerate(oq):
                    if not isinstance(q, dict) or not q.get("question") or not q.get("answer"):
                        err(rel, f"oa_questions[{i}] needs both 'question' and 'answer'")
            hk = d.get("hook")
            if hk is not None and (not isinstance(hk, dict) or not hk.get("scenario")):
                err(rel, "hook, if present, needs a non-empty 'scenario'")
            srcs = d.get("sources")
            if not isinstance(srcs, list) or not srcs:
                err(rel, "'sources' must be a non-empty list")
            else:
                for i, s in enumerate(srcs):
                    if not isinstance(s, str) or not s.startswith("http"):
                        err(rel, f"sources[{i}] is not a URL: {s!r}")
            if d.get("roadmap"):
                by_roadmap.setdefault(d["roadmap"], set()).add(d.get("slug"))
            continue

        # Reasoning (Logical Reasoning + Verbal) is a method-based lesson (kind: "reasoning"):
        # intuition + an ordered METHOD + one WORKED EXAMPLE. No formula, no discovery.
        # See content/PROMPT-reasoning.md.
        if d.get("kind") == "reasoning":
            mm = d.get("mental_model")
            if not isinstance(mm, dict) or not mm.get("intuition"):
                err(rel, "mental_model is required (object with a non-empty 'intuition')")
            method = d.get("method")
            if not isinstance(method, list) or len(method) < 2 or not all(isinstance(s, str) and s for s in method):
                err(rel, "method is required: an ordered list of >=2 non-empty step strings")
            we = d.get("worked_example")
            if (not isinstance(we, dict) or not we.get("problem") or not we.get("answer")
                    or not isinstance(we.get("steps"), list) or not we.get("steps")):
                err(rel, "worked_example is required: object with 'problem', non-empty 'steps' list, and 'answer'")
            cm = d.get("common_mistakes")
            if not isinstance(cm, list) or not cm:
                err(rel, "common_mistakes is required: a non-empty list")
            else:
                for i, c in enumerate(cm):
                    if not isinstance(c, dict) or not c.get("title") or not c.get("explanation"):
                        err(rel, f"common_mistakes[{i}] needs non-empty 'title' and 'explanation'")
            rq = d.get("recall_questions")
            if not isinstance(rq, list) or len(rq) < 3:
                err(rel, "recall_questions is required: >=3 items")
            else:
                for i, q in enumerate(rq):
                    if not isinstance(q, dict) or not q.get("q") or not q.get("answer"):
                        err(rel, f"recall_questions[{i}] needs both 'q' and 'answer'")
            oq = d.get("oa_questions")
            if not isinstance(oq, list) or len(oq) < 2:
                err(rel, "oa_questions is required: >=2 OA-style items")
            else:
                for i, q in enumerate(oq):
                    if not isinstance(q, dict) or not q.get("question") or not q.get("answer"):
                        err(rel, f"oa_questions[{i}] needs both 'question' and 'answer'")
            hk = d.get("hook")
            if hk is not None and (not isinstance(hk, dict) or not hk.get("scenario")):
                err(rel, "hook, if present, needs a non-empty 'scenario'")
            srcs = d.get("sources")
            if not isinstance(srcs, list) or not srcs:
                err(rel, "'sources' must be a non-empty list")
            else:
                for i, s in enumerate(srcs):
                    if not isinstance(s, str) or not s.startswith("http"):
                        err(rel, f"sources[{i}] is not a URL: {s!r}")
            if d.get("roadmap"):
                by_roadmap.setdefault(d["roadmap"], set()).add(d.get("slug"))
            continue

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
