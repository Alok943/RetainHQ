"""Contract tests for the LeetCode concept mapping.

`content/PROMPT-leetcode-mapping.md` states the rules the mapping run must obey,
but a rule that lives only in a prompt is a rule nothing enforces: the v1 run put
66 `role='primary'` rows on teaching-scaffold nodes (28 of them at confidence 0.9)
and it reached production unnoticed. These tests pin the contract in code.

See docs/IMPLEMENTATION-leetcode-log-capture.md §6.1 and
backend/scripts/sql/2026-07-30_fix_scaffold_primaries.sql.
"""
import json
from pathlib import Path

import pytest

from scripts.import_leetcode_catalog import SCAFFOLD_SLUGS

CONTENT_DIR = Path(__file__).parent.parent.parent / "content" / "leetcode-catalog"
PROMPT = Path(__file__).parent.parent.parent / "content" / "PROMPT-leetcode-mapping.md"


def test_scaffold_list_matches_the_prompt():
    """The frozenset in the importer must not drift from the prompt's ban list.

    They are two copies of one contract; a slug added to the prompt and not here
    would be silently importable as a primary.
    """
    assert PROMPT.exists(), "mapping prompt is the source of truth for this list"
    text = PROMPT.read_text(encoding="utf-8")
    missing = [s for s in SCAFFOLD_SLUGS if s not in text]
    assert not missing, f"slugs in SCAFFOLD_SLUGS but absent from the prompt: {missing}"
    assert len(SCAFFOLD_SLUGS) == 26, "the prompt bans exactly 26 scaffold slugs"


def test_scaffold_slugs_are_not_in_the_legal_vocabulary_as_primary():
    """node_slug_map.json carries all 124 concepts; 26 are scaffold, 98 legal."""
    path = CONTENT_DIR / "node_slug_map.json"
    if not path.exists():
        pytest.skip("catalog artifacts not present in this checkout")
    slug_to_title = json.loads(path.read_text(encoding="utf-8"))["slug_to_node_title"]
    legal = set(slug_to_title) - SCAFFOLD_SLUGS
    assert len(legal) == 98, f"expected 98 legal primary slugs, got {len(legal)}"
    # Every scaffold slug should still RESOLVE — they are legal as `supporting`.
    for slug in SCAFFOLD_SLUGS:
        assert slug in slug_to_title, f"{slug} must still map to a node for supporting use"


def test_mapping_file_names_no_scaffold_primary():
    """The committed mapping artifact itself must be clean.

    This is the check that would have caught the 66 rows before import. It reads
    the file, not the DB, so it runs in CI with no database.
    """
    path = CONTENT_DIR / "mapping.v1.json"
    if not path.exists():
        pytest.skip("mapping.v1.json not present in this checkout")
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = data if isinstance(data, list) else data.get("mappings", data.get("problems", []))

    offenders = [
        (r.get("external_id"), r.get("primary"))
        for r in rows
        if r.get("primary") in SCAFFOLD_SLUGS
    ]
    assert not offenders, (
        f"{len(offenders)} problems name a teaching-scaffold concept as `primary`; "
        "if nothing else fits the answer is 'out_of_scope'. First few: "
        f"{offenders[:10]}"
    )
