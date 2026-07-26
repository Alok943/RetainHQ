"""Turn the REVIEWED golden-review.txt into golden.json.

Usage:  python scripts/build_golden.py

Reads  content/leetcode-catalog/golden-review.txt  (your edits)
Writes content/leetcode-catalog/golden.json        (the gate input)

The labels in the review file start as Claude's draft. This script exists so the
human edit is the only thing that turns a draft into a benchmark - it validates
every label against the closed vocabulary, rejects teaching-scaffold slugs, and
prints exactly what you changed, so the diff is visible before it becomes truth.

NOTE: no labels live in this file, by design. A golden-set builder that carries
its own answers is how the 2026-07-21 run graded itself 100/100.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CAT = ROOT / "content" / "leetcode-catalog"
PROMPT = ROOT / "content" / "PROMPT-leetcode-mapping.md"

LINE = re.compile(r"^[?\s](\s*\d+)\s+([EMH])\s+(.+?)\s*\|\s*([a-z0-9_-]*)\s*$")


def load_vocab():
    """Vocabulary = first fenced block in the prompt; scaffold = second."""
    blocks = re.findall(r"```\n(.*?)```", PROMPT.read_text(encoding="utf-8"), re.S)
    if len(blocks) < 2:
        sys.exit("FAIL  could not find the vocabulary/scaffold blocks in the prompt")
    return set(blocks[0].split()), set(blocks[1].split())


def main() -> int:
    review = CAT / "golden-review.txt"
    if not review.exists():
        sys.exit(f"FAIL  missing {review}")
    vocab, scaffold = load_vocab()
    draft = {x["external_id"]: x for x in json.loads(
        (CAT / "golden.draft.json").read_text(encoding="utf-8"))}

    catalog = {x["external_id"]: x for x in json.loads(
        (CAT / "catalog.v1.json").read_text(encoding="utf-8"))["problems"]}
    blind = {k: v for k, v in catalog.items() if k not in draft}
    rows, errors, changed, blank = [], [], [], []
    for n, raw in enumerate(review.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        m = LINE.match(raw)
        if not m:
            errors.append(f"line {n}: unparseable -> {raw!r}")
            continue
        eid, label = int(m.group(1)), m.group(4)
        if not label:
            blank.append(eid)
            continue
        src = draft.get(eid) or blind.get(eid)
        if not src:
            errors.append(f"line {n}: id {eid} is in neither the draft nor the catalog")
            continue
        anchored = eid in draft
        if label != "out_of_scope":
            if label not in vocab:
                errors.append(f"line {n}: {eid} -> {label!r} is NOT in the 124-slug vocabulary")
                continue
            if label in scaffold:
                errors.append(f"line {n}: {eid} -> {label!r} is a teaching-scaffold slug "
                              f"(illegal as primary; pick a pattern, or out_of_scope)")
                continue
        if anchored and label != src["human_primary"]:
            changed.append((eid, src["title"], src["human_primary"], label))
        rows.append({"external_id": eid, "slug": src["slug"], "title": src["title"],
                     "difficulty": src["difficulty"], "human_primary": label,
                     "anchored": anchored})

    ids = [r["external_id"] for r in rows]
    if len(ids) != len(set(ids)):
        errors.append("duplicate ids in the review file")
    if len(rows) < 60:
        errors.append(f"only {len(rows)} rows parsed - the gate needs the full set")
    if blank:
        errors.append(f"{len(blank)} PART B row(s) still blank: {blank[:12]}"
                      f"{'...' if len(blank) > 12 else ''} - fill them from your own head")

    if errors:
        print("\n".join(f"FAIL  {e}" for e in errors))
        print(f"\nFAILED - {len(errors)} error(s). golden.json NOT written.")
        return 1

    rows.sort(key=lambda r: r["external_id"])
    (CAT / "golden.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")

    n_blind = sum(1 for r in rows if not r["anchored"])
    print(f"wrote golden.json - {len(rows)} problems "
          f"({len(rows)-n_blind} anchored / {n_blind} blind), {len(changed)} changed from the draft")
    print("  NOTE: report agreement SEPARATELY for anchored vs blind. Anchored rows were")
    print("  shown a label first, so high agreement there is partly anchoring, not skill.")
    for eid, title, old, new in changed:
        print(f"  #{eid:<5} {title[:38]:<38} {old} -> {new}")
    if not changed:
        print("\n  NOTE: zero changes in Part A. Plausible - it is famous problems with canonical")
        print("  answers - but it means Part A has little discriminating power. The BLIND rows")
        print("  carry the real signal; weight them accordingly when reading the gate result.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
