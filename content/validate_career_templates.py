#!/usr/bin/env python3
"""Validator for career-tree role templates (SPEC-career-coach-phase2.md §3.1).
Pure stdlib — no installs. Mirrors content/validate.py's err/warn/exit-code shape.

Run from the repo root:  python content/validate_career_templates.py
Checks every career-templates/<role_key>.v<N>.json for:
  - filename matches role_key + version
  - stable_key uniqueness (within the template — the load-bearing versioning
    primitive; never reused for a different concept across versions)
  - depends_on resolves to a real stable_key in the SAME template
  - no dependency cycles
  - priority 1-5, est_effort_min > 0
Exits non-zero if anything fails, so it can gate a commit.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent / "career-templates"
FILENAME_RE = re.compile(r"^([a-z][a-z0-9_]*)\.v(\d+)\.json$")
VERSION_RE = re.compile(r"^v(\d+)$")

# Target range from spec §3.2 — below ~40 the tree can't express real coverage;
# above ~70 the 5-minute confirm budget blows and users rubber-stamp it. This
# is UX guidance, not a hard structural rule, so it's a warning, not an error.
NODE_COUNT_SOFT_MIN = 40
NODE_COUNT_SOFT_MAX = 70

# Diagnostic (spec §4) needs 5-8 probes drawn from authored diagnostic_probe
# fields. Fewer than this and the diagnostic step can't hit its target size.
MIN_DIAGNOSTIC_PROBES = 5

errors = []
warnings = []


def err(f, msg):
    errors.append(f"  [FAIL] {f}: {msg}")


def warn(f, msg):
    warnings.append(f"  [warn] {f}: {msg}")


def _find_cycle(graph):
    """DFS cycle detection over stable_key -> [depends_on stable_keys].
    Returns one cycle (list of stable_keys) if found, else None."""
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {k: WHITE for k in graph}
    path = []

    def visit(node):
        color[node] = GRAY
        path.append(node)
        for dep in graph.get(node, ()):
            if dep not in color:
                continue  # unresolved dep already reported separately
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


def main():
    if not ROOT.exists():
        print(f"No {ROOT} directory found — nothing to validate.")
        return 0

    files = sorted(ROOT.glob("*.json"))
    for path in files:
        rel = path.relative_to(ROOT.parent)
        m = FILENAME_RE.match(path.name)
        if not m:
            err(rel, "filename must match '<role_key>.v<N>.json' (lowercase, digits, underscores)")
            continue
        file_role_key, file_version_num = m.group(1), m.group(2)

        try:
            d = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            err(rel, f"invalid JSON: {e}")
            continue

        role_key = d.get("role_key")
        if role_key != file_role_key:
            err(rel, f"role_key '{role_key}' does not match filename's '{file_role_key}'")

        version = d.get("version")
        vm = VERSION_RE.match(version or "")
        if not vm:
            err(rel, f"version '{version}' must look like 'v<N>'")
        elif vm.group(1) != file_version_num:
            err(rel, f"version '{version}' does not match filename's 'v{file_version_num}'")

        if not d.get("title"):
            err(rel, "missing required field 'title'")

        subjects = d.get("subjects")
        if not isinstance(subjects, list) or not subjects:
            err(rel, "'subjects' must be a non-empty list")
            continue

        stable_keys_seen = {}  # stable_key -> subject key(s) it appeared under
        graph = {}
        node_meta = {}  # stable_key -> node dict, for priority/effort/probe checks
        subject_keys_seen = set()

        for si, subject in enumerate(subjects):
            skey = subject.get("key")
            if not skey:
                err(rel, f"subjects[{si}] missing 'key'")
            elif skey in subject_keys_seen:
                err(rel, f"subjects[{si}] duplicate subject key '{skey}'")
            else:
                subject_keys_seen.add(skey)

            if not subject.get("title"):
                err(rel, f"subjects[{si}] ('{skey}') missing 'title'")

            default_priority = subject.get("default_priority")
            if not isinstance(default_priority, int) or not (1 <= default_priority <= 5):
                err(rel, f"subjects[{si}] ('{skey}') default_priority must be an int 1-5")

            nodes = subject.get("nodes")
            if not isinstance(nodes, list) or not nodes:
                err(rel, f"subjects[{si}] ('{skey}') 'nodes' must be a non-empty list")
                continue

            for ni, node in enumerate(nodes):
                where = f"subjects[{si}] ('{skey}') nodes[{ni}]"
                stable_key = node.get("stable_key")
                if not stable_key:
                    err(rel, f"{where} missing 'stable_key'")
                    continue
                if stable_key in stable_keys_seen:
                    err(rel, f"duplicate stable_key '{stable_key}' (first seen under '{stable_keys_seen[stable_key]}', again under '{skey}')")
                else:
                    stable_keys_seen[stable_key] = skey
                    graph[stable_key] = list(node.get("depends_on") or [])
                    node_meta[stable_key] = node

                if not node.get("title"):
                    err(rel, f"{where} ('{stable_key}') missing 'title'")

                priority = node.get("priority")
                if not isinstance(priority, int) or not (1 <= priority <= 5):
                    err(rel, f"{where} ('{stable_key}') priority must be an int 1-5")

                effort = node.get("est_effort_min")
                if not isinstance(effort, int) or effort <= 0:
                    err(rel, f"{where} ('{stable_key}') est_effort_min must be a positive int")

                # diagnostic_answer is the grading rubric (services/career_tree's
                # diagnostic step feeds it to grader.grade_recall as key_memory) —
                # a probe with no reference answer can't be graded at all.
                if node.get("diagnostic_probe") and not node.get("diagnostic_answer"):
                    err(rel, f"{where} ('{stable_key}') has diagnostic_probe but no diagnostic_answer")

        # depends_on resolution — every reference must exist in THIS template.
        for stable_key, deps in graph.items():
            for dep in deps:
                if dep not in stable_keys_seen:
                    err(rel, f"'{stable_key}' depends_on unresolved stable_key '{dep}'")

        cycle = _find_cycle(graph)
        if cycle:
            err(rel, f"dependency cycle: {' -> '.join(cycle)}")

        total_nodes = len(stable_keys_seen)
        if total_nodes < NODE_COUNT_SOFT_MIN or total_nodes > NODE_COUNT_SOFT_MAX:
            warn(rel, f"{total_nodes} nodes — outside the {NODE_COUNT_SOFT_MIN}-{NODE_COUNT_SOFT_MAX} target range (spec §3.2)")

        probe_count = sum(1 for n in node_meta.values() if n.get("diagnostic_probe"))
        if probe_count < MIN_DIAGNOSTIC_PROBES:
            warn(rel, f"only {probe_count} node(s) have a diagnostic_probe — diagnostic needs {MIN_DIAGNOSTIC_PROBES}-8")

        # Probe spread (SPEC-career-templates-v2 §4): diagnostic selection is
        # round-robin per subject, so a high-priority subject with zero probes
        # silently gets no diagnostic coverage at all. Warning, not error —
        # some subjects legitimately don't probe well (e.g. interview prep).
        for subject in subjects:
            if not isinstance(subject, dict):
                continue
            if (subject.get("default_priority") or 0) >= 4 and not any(
                n.get("diagnostic_probe") and n.get("diagnostic_answer")
                for n in subject.get("nodes", []) if isinstance(n, dict)
            ):
                warn(rel, f"subject '{subject.get('key')}' has default_priority >= 4 but no probe-bearing node — it gets zero diagnostic coverage")

    print(f"Checked {len(files)} career template(s).\n")
    if warnings:
        print("Warnings:")
        print("\n".join(warnings), "\n")
    if errors:
        print("Errors:")
        print("\n".join(errors))
        print(f"\n{len(errors)} error(s).")
        return 1
    print("All career templates valid. [OK]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
