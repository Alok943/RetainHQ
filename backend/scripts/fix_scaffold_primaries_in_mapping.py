"""Patch content/leetcode-catalog/mapping.v1.json to remove the 66 illegal
teaching-scaffold `primary` assignments.

The DB fix (scripts/sql/2026-07-30_fix_scaffold_primaries.sql) repairs production.
This repairs the committed artifact, so the next `import_leetcode_catalog.py` run
does not reintroduce them — the importer now refuses outright on a scaffold
primary, so without this patch the import would simply fail.

Same 40 reassignments / 26 out_of_scope as the SQL. Reclassified 2026-07-30 by
Claude (Opus 5); stamped `reviewed_by='claude-opus-5:scaffold-fix'`, deliberately
NOT 'human' (HANDOFF-leetcode-mapping-run.md rule 3 — no self-grading).

Idempotent. Run:  python backend/scripts/fix_scaffold_primaries_in_mapping.py
"""
import json
from pathlib import Path

MAPPING = Path(__file__).parent.parent.parent / "content" / "leetcode-catalog" / "mapping.v1.json"
STAMP = "claude-opus-5:scaffold-fix"

# external_id -> (new primary slug, confidence band)
REASSIGN = {
    271: ("designing-data-structures", "high"),
    280: ("why-greedy-works", "high"),
    319: ("combinatorics-and-counting", "medium"),
    326: ("gcd-lcm-and-modular-arithmetic", "high"),
    349: ("hash-tables", "high"),
    356: ("hash-tables", "high"),
    395: ("sliding-window-variable", "high"),
    414: ("top-k-with-a-heap", "medium"),
    418: ("memoization-top-down", "medium"),
    427: ("recursion-tree", "high"),
    442: ("frequency-arrays", "high"),
    448: ("frequency-arrays", "high"),
    944: ("2d-arrays-and-matrices", "high"),
    985: ("prefix-sums", "medium"),
    997: ("frequency-arrays", "high"),
    1437: ("two-pointers", "medium"),
    1446: ("two-pointers-on-strings", "medium"),
    1808: ("gcd-lcm-and-modular-arithmetic", "high"),
    1827: ("why-greedy-works", "high"),
    1840: ("why-greedy-works", "medium"),
    1846: ("why-greedy-works", "high"),
    1864: ("why-greedy-works", "high"),
    1874: ("why-greedy-works", "high"),
    1881: ("why-greedy-works", "high"),
    1899: ("why-greedy-works", "high"),
    1903: ("why-greedy-works", "high"),
    1909: ("why-greedy-works", "medium"),
    1913: ("why-greedy-works", "medium"),
    1921: ("why-greedy-works", "high"),
    1922: ("gcd-lcm-and-modular-arithmetic", "high"),
    1927: ("why-greedy-works", "high"),
    1936: ("why-greedy-works", "high"),
    1946: ("why-greedy-works", "high"),
    2860: ("combinatorics-and-counting", "medium"),
    2864: ("why-greedy-works", "high"),
    2899: ("stack-fundamentals", "high"),
    2908: ("prefix-sums", "high"),
    2914: ("why-greedy-works", "high"),
    2934: ("why-greedy-works", "medium"),
    2937: ("two-pointers-on-strings", "high"),
}

# No legal primary exists — implementation / simulation / formula problems.
OUT_OF_SCOPE = {
    412, 434, 806, 824, 831, 833, 1427, 1816, 1822, 1828,
    1844, 1848, 1859, 1860, 1869, 1880, 1904, 1920, 1925, 1929,
    1933, 1945, 2855, 2942, 2951, 2960,
}


def main() -> None:
    data = json.loads(MAPPING.read_text(encoding="utf-8"))
    rows = data["mappings"]

    reassigned = dropped = 0
    for row in rows:
        ext = row.get("external_id")
        if ext in REASSIGN:
            slug, band = REASSIGN[ext]
            # Don't leave the new primary duplicated in supporting/alternatives —
            # the importer tolerates it, but a row that lists its own primary as an
            # alternative is nonsense to read.
            for key in ("supporting", "alternatives"):
                if isinstance(row.get(key), list) and slug in row[key]:
                    row[key] = [s for s in row[key] if s != slug]
            row["primary"] = slug
            row["confidence"] = band
            row["reviewed_by"] = STAMP
            reassigned += 1
        elif ext in OUT_OF_SCOPE:
            row["primary"] = "out_of_scope"
            row["confidence"] = "low"
            row["reviewed_by"] = STAMP
            dropped += 1

    if reassigned != len(REASSIGN) or dropped != len(OUT_OF_SCOPE):
        raise SystemExit(
            f"expected {len(REASSIGN)} reassigned / {len(OUT_OF_SCOPE)} out_of_scope, "
            f"got {reassigned} / {dropped} — external_ids missing from the mapping file?"
        )

    counts = data.setdefault("counts", {})
    counts["mapped"] = sum(1 for r in rows if r.get("primary") not in (None, "out_of_scope"))
    counts["out_of_scope"] = sum(1 for r in rows if r.get("primary") == "out_of_scope")
    data["mapping_version"] = "v1.1"
    data["scaffold_fix"] = {
        "applied_at": "2026-07-30",
        "by": STAMP,
        "reassigned": reassigned,
        "to_out_of_scope": dropped,
        "note": "PROMPT-leetcode-mapping.md bans 26 scaffold slugs as `primary`; v1 broke it 66x.",
    }

    MAPPING.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"OK: {reassigned} reassigned, {dropped} -> out_of_scope; "
          f"mapped={counts['mapped']}, out_of_scope={counts['out_of_scope']}")


if __name__ == "__main__":
    main()
