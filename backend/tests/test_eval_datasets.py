"""Schema-only check for backend/evals/datasets/*.jsonl.

Deliberately free of any live-model call — the eval RUNNER (`python -m
evals.run`) is a separate, manually-invoked tool that costs real tokens/
latency and is never part of this suite. This just proves every dataset file
parses against its case schema and has no duplicate ids, so a malformed
dataset fails fast in CI instead of at eval-run time.
"""
from pathlib import Path

import pytest

from evals.schemas import SUITE_SCHEMAS

DATASET_DIR = Path(__file__).parent.parent / "evals" / "datasets"


@pytest.mark.parametrize("suite_name,model_cls", SUITE_SCHEMAS.items())
def test_dataset_parses_and_has_unique_ids(suite_name, model_cls):
    path = DATASET_DIR / f"{suite_name}.jsonl"
    assert path.exists(), f"missing dataset file: {path}"

    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert lines, f"{suite_name} dataset is empty"

    seen_ids = set()
    for line_no, line in enumerate(lines, 1):
        case = model_cls.model_validate_json(line)
        assert case.id not in seen_ids, f"{suite_name}.jsonl:{line_no}: duplicate case id {case.id!r}"
        seen_ids.add(case.id)
