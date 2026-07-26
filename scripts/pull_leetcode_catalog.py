#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pull_leetcode_catalog.py
========================
Standalone script that fetches LeetCode problem *metadata* from two
independent public endpoints, cross-checks them, and writes a versioned
catalog plus conflict report.

Dependencies: requests (stdlib otherwise).
Spec: content/HANDOFF-leetcode-catalog.md
"""

import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Force UTF-8 output on Windows (avoids cp1252 UnicodeEncodeError)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

try:
    import requests
except ImportError:
    sys.exit("ERROR: 'requests' is required.  pip install requests")

# ─── constants ───────────────────────────────────────────────────────────────

GRAPHQL_URL = "https://leetcode.com/graphql"
REST_URL = "https://leetcode.com/api/problems/all/"
USER_AGENT = "RetainHQ-catalog-seed/1.0 (+https://retainhq.app)"
PAGE_SIZE = 100
REQUEST_DELAY = 2.0          # seconds between requests (≥ 2 s)
MAX_RETRIES = 2
BACKOFF_BASE = 4             # 4 s, 8 s

DIFFICULTY_MAP = {1: "easy", 2: "medium", 3: "hard"}
SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
ALLOWED_KEYS = {"source", "external_id", "slug", "title", "difficulty",
                "tags", "url", "acceptance", "paid_only"}

# Sanity thresholds (§1.5)
MIN_ACCEPTED = 2500
MAX_CONFLICT_RATIO = 0.02
MAX_VALUE_LEN = 300

GRAPHQL_QUERY = """
query problemsetQuestionList($categorySlug: String, $limit: Int, $skip: Int, $filters: QuestionListFilterInput) {
  problemsetQuestionList: questionList(categorySlug: $categorySlug, limit: $limit, skip: $skip, filters: $filters) {
    total: totalNum
    questions: data {
      frontendQuestionId: questionFrontendId
      title
      titleSlug
      difficulty
      acRate
      isPaidOnly
      topicTags { name slug }
    }
  }
}
""".strip()

# ─── output paths (relative to repo root) ───────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parent.parent
CATALOG_DIR = REPO_ROOT / "content" / "leetcode-catalog"
RAW_DIR = CATALOG_DIR / "raw"
CATALOG_PATH = CATALOG_DIR / "catalog.v1.json"
CONFLICTS_PATH = CATALOG_DIR / "catalog-conflicts.v1.json"


# ─── helpers ─────────────────────────────────────────────────────────────────

def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": USER_AGENT})
    return s


def _request_with_retry(session: requests.Session, method: str, url: str,
                         **kwargs) -> requests.Response:
    """Issue a request with up to MAX_RETRIES retries + exponential backoff.
    Aborts the whole run on a 3rd failure."""
    last_exc = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = session.request(method, url, timeout=30, **kwargs)
            resp.raise_for_status()
            return resp
        except (requests.RequestException, Exception) as exc:
            last_exc = exc
            if attempt < MAX_RETRIES:
                wait = BACKOFF_BASE * (2 ** attempt)
                print(f"  ⚠ attempt {attempt + 1} failed ({exc}), retrying in {wait}s …")
                time.sleep(wait)
            else:
                sys.exit(f"ABORT: request to {url} failed after {MAX_RETRIES + 1} attempts.\n"
                         f"  Last error: {last_exc}")
    # unreachable, but keeps type-checker happy
    raise RuntimeError("unreachable")


def _delay():
    time.sleep(REQUEST_DELAY)


# ─── Source A: GraphQL ───────────────────────────────────────────────────────

def fetch_graphql(session: requests.Session) -> list[dict]:
    """Paginate the GraphQL endpoint, saving raw responses. Returns the
    list of question dicts exactly as received."""
    all_questions: list[dict] = []
    raw_pages: list[tuple[str, dict]] = []

    # ── probe request (limit 1, skip 0) to confirm schema ──
    print("Source A — GraphQL probe (limit=1, skip=0) …")
    probe_resp = _request_with_retry(
        session, "POST", GRAPHQL_URL,
        json={"query": GRAPHQL_QUERY,
              "variables": {"categorySlug": "", "skip": 0,
                            "limit": 1, "filters": {}}},
    )
    probe_data = probe_resp.json()

    # Validate shape
    pql = probe_data.get("data", {}).get("problemsetQuestionList")
    if pql is None:
        # Schema may have drifted — dump the response and abort
        fname = "graphql-probe-error.json"
        _save_raw(fname, probe_data)
        sys.exit(f"ABORT: GraphQL schema appears to have drifted.\n"
                 f"  Expected data.problemsetQuestionList, got keys: "
                 f"{list(probe_data.get('data', {}).keys()) if 'data' in probe_data else list(probe_data.keys())}\n"
                 f"  Raw response saved to raw/{fname}")

    total = pql["total"]
    print(f"  Schema OK.  Total problems reported: {total}")
    raw_pages.append(("graphql-skip-0000.json", probe_data))
    all_questions.extend(pql.get("questions", []))

    _delay()

    # ── full sweep ──
    skip = PAGE_SIZE  # we already got page 0 with limit=1, re-fetch full page
    # Actually, the probe was limit=1. Re-fetch page 0 fully.
    # Reset and start from 0 with full PAGE_SIZE.
    all_questions.clear()
    raw_pages_data: list[tuple[str, dict]] = []

    skip = 0
    page_num = 0
    while skip < total:
        print(f"  Fetching skip={skip} (page {page_num}) …")
        resp = _request_with_retry(
            session, "POST", GRAPHQL_URL,
            json={"query": GRAPHQL_QUERY,
                  "variables": {"categorySlug": "", "skip": skip,
                                "limit": PAGE_SIZE, "filters": {}}},
        )
        data = resp.json()
        fname = f"graphql-skip-{skip:04d}.json"
        raw_pages_data.append((fname, data))

        questions = (data.get("data", {})
                         .get("problemsetQuestionList", {})
                         .get("questions", []))
        if not questions:
            break
        all_questions.extend(questions)

        skip += PAGE_SIZE
        page_num += 1
        if skip < total:
            _delay()

    # Save raw pages
    for fname, payload in raw_pages_data:
        _save_raw(fname, payload)

    print(f"  Source A fetched: {len(all_questions)} questions across {page_num} pages.")
    return all_questions


# ─── Source B: REST ──────────────────────────────────────────────────────────

def fetch_rest(session: requests.Session) -> list[dict]:
    """Fetch the legacy REST endpoint. Returns stat_status_pairs as-is."""
    print("Source B — REST /api/problems/all/ …")
    resp = _request_with_retry(session, "GET", REST_URL)
    data = resp.json()
    _save_raw("rest-all.json", data)
    pairs = data.get("stat_status_pairs", [])
    print(f"  Source B fetched: {len(pairs)} entries.")
    return pairs


# ─── raw file saving ────────────────────────────────────────────────────────

def _save_raw(filename: str, data: dict):
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_DIR / filename
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8", newline="\n")


# ─── normalisation ───────────────────────────────────────────────────────────

def normalise_a(questions: list[dict]) -> dict[int, dict]:
    """Return {external_id: normalised_row} from Source A."""
    result: dict[int, dict] = {}
    for q in questions:
        eid = int(q["frontendQuestionId"])
        diff = q["difficulty"].lower()
        tags = sorted(set(t["slug"] for t in (q.get("topicTags") or [])))
        ac_rate = q.get("acRate")
        acceptance = round(ac_rate / 100.0, 3) if ac_rate is not None else None
        result[eid] = {
            "external_id": eid,
            "title": q["title"],
            "slug": q["titleSlug"],
            "difficulty": diff,
            "tags": tags,
            "acceptance": acceptance,
            "paid_only": bool(q.get("isPaidOnly", False)),
        }
    return result


def normalise_b(pairs: list[dict]) -> dict[int, dict]:
    """Return {external_id: normalised_row} from Source B."""
    result: dict[int, dict] = {}
    for entry in pairs:
        stat = entry.get("stat", {})
        diff_obj = entry.get("difficulty", {})
        eid = int(stat["frontend_question_id"])
        diff_level = diff_obj.get("level")
        diff = DIFFICULTY_MAP.get(diff_level, f"unknown-{diff_level}")
        total_acs = stat.get("total_acs", 0)
        total_sub = stat.get("total_submitted", 0)
        acceptance_b = round(total_acs / total_sub, 3) if total_sub > 0 else None
        result[eid] = {
            "external_id": eid,
            "slug": stat.get("question__title_slug", ""),
            "difficulty": diff,
            "paid_only": bool(entry.get("paid_only", False)),
            "acceptance_b": acceptance_b,
            "title_b": stat.get("question__title", ""),
        }
    return result


# ─── cross-check & merge ────────────────────────────────────────────────────

def cross_check(a_map: dict[int, dict], b_map: dict[int, dict]):
    """Apply §1.3 trust mechanism.  Returns (accepted_list, conflicts_list,
    acceptance_divergences)."""
    all_ids = sorted(set(a_map.keys()) | set(b_map.keys()))
    accepted: list[dict] = []
    conflicts: list[dict] = []
    acceptance_divergences: list[dict] = []

    for eid in all_ids:
        in_a = eid in a_map
        in_b = eid in b_map

        if in_a and not in_b:
            conflicts.append({
                "external_id": eid,
                "reason": "missing_in_b",
                "source_a": a_map[eid],
                "source_b": None,
            })
            continue
        if in_b and not in_a:
            conflicts.append({
                "external_id": eid,
                "reason": "missing_in_a",
                "source_a": None,
                "source_b": b_map[eid],
            })
            continue

        # Both present — compare slug, difficulty, paid_only
        ra, rb = a_map[eid], b_map[eid]
        mismatches = []
        if ra["slug"] != rb["slug"]:
            mismatches.append(f"slug: A={ra['slug']!r} B={rb['slug']!r}")
        if ra["difficulty"] != rb["difficulty"]:
            mismatches.append(f"difficulty: A={ra['difficulty']!r} B={rb['difficulty']!r}")
        if ra["paid_only"] != rb["paid_only"]:
            mismatches.append(f"paid_only: A={ra['paid_only']} B={rb['paid_only']}")

        if mismatches:
            conflicts.append({
                "external_id": eid,
                "reason": "field_mismatch",
                "mismatches": mismatches,
                "source_a": ra,
                "source_b": rb,
            })
            continue

        # ── Accepted row ──
        # Check acceptance divergence (cosmetic, never blocks)
        acc_a = ra.get("acceptance")
        acc_b = rb.get("acceptance_b")
        if acc_a is not None and acc_b is not None:
            if abs(acc_a - acc_b) > 0.02:
                acceptance_divergences.append({
                    "external_id": eid,
                    "slug": ra["slug"],
                    "acceptance_a": acc_a,
                    "acceptance_b": acc_b,
                    "diff_pp": round(abs(acc_a - acc_b) * 100, 1),
                })

        # Build final row — acceptance from A
        accepted.append({
            "source": "leetcode",
            "external_id": eid,
            "slug": ra["slug"],
            "title": ra["title"],
            "difficulty": ra["difficulty"],
            "tags": ra["tags"],
            "url": f"https://leetcode.com/problems/{ra['slug']}/",
            "acceptance": acc_a,
            "paid_only": ra["paid_only"],
        })

    accepted.sort(key=lambda r: r["external_id"])
    conflicts.sort(key=lambda r: r["external_id"])
    return accepted, conflicts, acceptance_divergences


# ─── self-checks (§1.5) ─────────────────────────────────────────────────────

def run_self_checks(accepted: list[dict], conflicts: list[dict],
                    total_unique: int) -> list[str]:
    """Return list of failure messages. Empty = all passed."""
    failures: list[str] = []

    # 1. external_id unique
    ids = [r["external_id"] for r in accepted]
    if len(ids) != len(set(ids)):
        dup_ids = [x for x in ids if ids.count(x) > 1]
        failures.append(f"Duplicate external_id(s) in accepted rows: {sorted(set(dup_ids))[:10]}")

    # 2. difficulty enum, slug regex
    valid_diffs = {"easy", "medium", "hard"}
    for r in accepted:
        if r["difficulty"] not in valid_diffs:
            failures.append(f"  ID {r['external_id']}: bad difficulty {r['difficulty']!r}")
        if not SLUG_RE.match(r["slug"]):
            failures.append(f"  ID {r['external_id']}: bad slug {r['slug']!r}")

    # 3. Accepted count ≥ 2500
    if len(accepted) < MIN_ACCEPTED:
        failures.append(f"Accepted count {len(accepted)} < {MIN_ACCEPTED} — "
                        "pagination may have silently truncated.")

    # 4. Conflicts ≤ 2% of total
    if total_unique > 0 and len(conflicts) / total_unique > MAX_CONFLICT_RATIO:
        pct = round(len(conflicts) / total_unique * 100, 1)
        failures.append(f"Conflict ratio {pct}% > {MAX_CONFLICT_RATIO * 100}% "
                        f"({len(conflicts)} / {total_unique})")

    # 5. No extra keys
    for r in accepted:
        extra = set(r.keys()) - ALLOWED_KEYS
        if extra:
            failures.append(f"  ID {r['external_id']}: unexpected keys {extra}")

    # 6. No value > 300 chars
    for r in accepted:
        for k, v in r.items():
            if isinstance(v, str) and len(v) > MAX_VALUE_LEN:
                failures.append(f"  ID {r['external_id']}: field {k!r} is {len(v)} chars "
                                f"(>{MAX_VALUE_LEN}) — possible description leak")
            if isinstance(v, list):
                for item in v:
                    if isinstance(item, str) and len(item) > MAX_VALUE_LEN:
                        failures.append(f"  ID {r['external_id']}: tag {item!r} is {len(item)} chars")

    return failures


# ─── write artifacts ─────────────────────────────────────────────────────────

def write_catalog(accepted: list[dict], conflicts: list[dict],
                  source_a_count: int, source_b_count: int,
                  pulled_at: str):
    CATALOG_DIR.mkdir(parents=True, exist_ok=True)

    catalog = {
        "catalog_version": "v1",
        "source": "leetcode",
        "pulled_at": pulled_at,
        "counts": {
            "accepted": len(accepted),
            "conflicts": len(conflicts),
            "source_a": source_a_count,
            "source_b": source_b_count,
        },
        "problems": accepted,
    }
    CATALOG_PATH.write_text(
        json.dumps(catalog, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8", newline="\n",
    )
    print(f"  ✓ Wrote {CATALOG_PATH.relative_to(REPO_ROOT)}")

    CONFLICTS_PATH.write_text(
        json.dumps(conflicts, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8", newline="\n",
    )
    print(f"  ✓ Wrote {CONFLICTS_PATH.relative_to(REPO_ROOT)}")


# --- main --------------------------------------------------------------------

def main():
    t0 = time.monotonic()
    pulled_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"=== LeetCode Catalog Pull --- {pulled_at} ===\n")

    session = _session()
    request_count = 0

    # --- Source A ---
    a_raw = fetch_graphql(session)
    # Count requests: 1 probe + ceil(total/PAGE_SIZE) pages
    # (actual count tracked inside fetch_graphql, approximate here)
    _delay()

    # --- Source B ---
    b_raw = fetch_rest(session)

    # --- Normalise ---
    a_map = normalise_a(a_raw)
    b_map = normalise_b(b_raw)
    print(f"\nNormalised: A={len(a_map)}, B={len(b_map)}")

    # --- Cross-check ---
    accepted, conflicts, acc_divs = cross_check(a_map, b_map)
    total_unique = len(set(a_map.keys()) | set(b_map.keys()))
    print(f"Cross-check: {len(accepted)} accepted, {len(conflicts)} conflicts, "
          f"{len(acc_divs)} acceptance divergences > 2pp")

    # --- Self-checks ---
    print("\nRunning self-checks ...")
    failures = run_self_checks(accepted, conflicts, total_unique)
    if failures:
        print("\n! SELF-CHECK FAILURES — aborting (no files written):")
        for f in failures:
            print(f"    {f}")
        sys.exit(1)
    print("  * All self-checks passed.")

    # --- Write artifacts ---
    print("\nWriting artifacts ...")
    write_catalog(accepted, conflicts, len(a_map), len(b_map), pulled_at)

    elapsed = time.monotonic() - t0
    print(f"\n=== Done in {elapsed:.1f}s ===")
    print(f"  Accepted:  {len(accepted)}")
    print(f"  Conflicts: {len(conflicts)}")
    print(f"  Acc divs:  {len(acc_divs)}")

    # Print summary for report generation
    print("\n-- Summary for report --")
    print(f"pulled_at: {pulled_at}")
    print(f"wall_clock: {elapsed:.1f}s")
    print(f"source_a_total: {len(a_map)}")
    print(f"source_b_total: {len(b_map)}")
    print(f"accepted: {len(accepted)}")
    print(f"conflicts: {len(conflicts)}")
    conflict_reasons: dict[str, int] = {}
    for c in conflicts:
        r = c.get("reason", "unknown")
        conflict_reasons[r] = conflict_reasons.get(r, 0) + 1
    for reason, count in sorted(conflict_reasons.items()):
        print(f"  conflict_reason_{reason}: {count}")
    print(f"acceptance_divergences_gt_2pp: {len(acc_divs)}")
    if acc_divs:
        for d in acc_divs[:10]:
            print(f"  ID {d['external_id']} ({d['slug']}): "
                  f"A={d['acceptance_a']:.3f} B={d['acceptance_b']:.3f} "
                  f"Δ={d['diff_pp']:.1f}pp")
        if len(acc_divs) > 10:
            print(f"  … and {len(acc_divs) - 10} more")

    gate_path = REPO_ROOT / "content" / "validate_leetcode_catalog.py"
    if gate_path.exists():
        print(f"\nGate validator found at {gate_path.relative_to(REPO_ROOT)}")
        print("Run it separately:  python content/validate_leetcode_catalog.py")
    else:
        print("\n⚠ Gate validator content/validate_leetcode_catalog.py not found (expected per §Pass 0).")


if __name__ == "__main__":
    main()
