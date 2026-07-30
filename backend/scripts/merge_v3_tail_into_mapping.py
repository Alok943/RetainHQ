"""Merge mapping.v3-tail.json's 797 decisions into mapping.v1.json in place.

import_leetcode_catalog.py reads mapping.v1.json only, so this is what actually
makes pass 3's re-classification importable into problem_concepts — same
pattern as fix_scaffold_primaries_in_mapping.py before it.

Only `primary` / `confidence` / `reason` / `reviewed_by` are touched. `supporting`
and `alternatives` are left exactly as v1 had them: pass 3 was scoped to `primary`
only (HANDOFF-leetcode-mapping-rerun.md §2 item 5), and its `considered` field is
a "next-best guess", not a verified co-equal approach — writing it into
`alternatives` would inject unverified rows into a field whose role='alternative'
means "each independently solves it" (SPEC-leetcode-retention.md §3.2.-1). It
stays recorded in mapping.v3-tail.json for anyone auditing a specific problem.

Applies to all 797 rows, including the ones where v3 agreed with v1: pass 3 is
an independently-verified judgment for every one of these 797 rows (that was the
point of the re-run), so its confidence/reason/reviewed_by are the better record
even where the primary concept itself didn't change.

Idempotent — the guard at the end fails loudly if run against an already-merged
file (reviewed_by would already be the stamp) rather than silently no-op'ing,
so a re-run mid-review doesn't look like it did something it didn't.

Run:  python backend/scripts/merge_v3_tail_into_mapping.py
"""
import json
from pathlib import Path

CAT = Path(__file__).parent.parent.parent / "content" / "leetcode-catalog"
MAPPING = CAT / "mapping.v1.json"
V3 = CAT / "mapping.v3-tail.json"
STAMP = "pass3-blind:gemini-3.1-pro"


def main() -> None:
    data = json.loads(MAPPING.read_text(encoding="utf-8"))
    rows = {r["external_id"]: r for r in data["mappings"]}

    v3 = json.loads(V3.read_text(encoding="utf-8"))
    decisions = v3["decisions"]
    if v3.get("input_rows") != 797 or len(decisions) != 797:
        raise SystemExit(f"expected 797/797, got input_rows={v3.get('input_rows')} decisions={len(decisions)}")

    already = sum(1 for d in decisions if rows.get(d["external_id"], {}).get("reviewed_by") == STAMP)
    if already:
        raise SystemExit(f"{already} rows already carry the {STAMP!r} stamp — this file looks already merged; aborting.")

    applied = missing = 0
    for d in decisions:
        row = rows.get(d["external_id"])
        if row is None:
            missing += 1
            print(f"  WARNING: #{d['external_id']} in v3 but not in mapping.v1.json — skipped")
            continue
        row["primary"] = d["primary"]
        row["confidence"] = d["confidence"]
        row["reason"] = d["reason"]
        row["reviewed_by"] = STAMP
        applied += 1

    if applied != 797:
        raise SystemExit(f"applied {applied}/797 — {missing} missing from mapping.v1.json, investigate before trusting this merge")

    data["mapping_version"] = "v1.2"
    data["v3_tail_merge"] = {
        "applied_at": "2026-07-30",
        "source": "mapping.v3-tail.json",
        "rows_merged": applied,
        "note": (
            "797-row low-confidence tail re-classified against a blinded work set "
            "(no prior assignment included), verified independently before merge "
            "(0% reason-copy from v1, 53.5% v1-agreement, 68.8% on a withheld golden "
            "subset — none matching the rejected pass-2 passthrough/lookup signature). "
            "37 of the 797 (external_id 3811-3994, the newest problems) are an "
            "accepted end-of-batch fallback: out_of_scope/low rather than a genuine "
            "per-problem judgment — see mapping.v3-tail.NOTES.md."
        ),
    }

    MAPPING.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"OK: merged {applied} rows into {MAPPING.relative_to(MAPPING.parent.parent.parent)}, mapping_version -> v1.2")


if __name__ == "__main__":
    main()
