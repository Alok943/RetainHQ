"""CLI: `python -m evals.run [suite ...]` (run from `backend/`).

Runs one or more eval suites against the LIVE model and writes a markdown
report to evals/reports/. Exits non-zero if any (non-skipped) suite fails its
thresholds. Costs real tokens/latency — never part of the default `pytest`
run; `tests/test_eval_datasets.py` covers the free schema-only check.

Examples:
    python -m evals.run              # all suites
    python -m evals.run grader       # just the grader suite
"""
import argparse
import asyncio
import datetime
import json
import sys
from pathlib import Path

from evals import checks, schemas

DATASET_DIR = Path(__file__).parent / "datasets"
REPORT_DIR = Path(__file__).parent / "reports"

SUITES = {
    "grader": (schemas.GraderCase, checks.check_grader),
    "mcq_items": (schemas.MCQItemCase, checks.check_mcq_items),
    "answerable": (schemas.AnswerableCase, checks.check_answerable),
    "leetcode_statements": (schemas.LeetcodeStatementCase, checks.check_leetcode_statements),
}


def load_cases(suite_name: str):
    model_cls, _ = SUITES[suite_name]
    path = DATASET_DIR / f"{suite_name}.jsonl"
    cases = []
    with path.open(encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                cases.append(model_cls.model_validate_json(line))
            except Exception as e:
                raise ValueError(f"{path}:{line_no}: {e}") from e
    return cases


def _fmt(v):
    return f"{v:.3f}" if isinstance(v, float) else str(v)


def write_report(suite_name: str, result: dict) -> Path:
    REPORT_DIR.mkdir(exist_ok=True)
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d-%H%M%S")
    path = REPORT_DIR / f"{suite_name}-{ts}.md"

    lines = [f"# Eval report — {suite_name}", "", f"Run at {ts} UTC · {result.get('total_cases', 0)} cases", ""]

    if result.get("skipped"):
        lines.append("**SKIPPED**")
        for note in result.get("notes", []):
            lines.append(f"- {note}")
    else:
        lines.append("## Metrics")
        for k, v in result.get("metrics", {}).items():
            lines.append(f"- **{k}**: {_fmt(v)}")
        lines.append("")
        lines.append("## Thresholds")
        for k, v in result.get("thresholds", {}).items():
            lines.append(f"- {k} {v}")
        lines.append("")
        lines.append(f"## Result: {'PASS' if result['passed'] else 'FAIL'}")

        flagged = [
            r for r in result.get("case_results", [])
            if r.get("false_accept") or r.get("false_reject") or r.get("error")
            or r.get("structural_failures") or r.get("judged_valid") is False
            or r.get("judged_answerable") is False
        ]
        if flagged:
            lines.append("")
            lines.append("## Flagged cases")
            for r in flagged:
                lines.append(f"- `{json.dumps(r)}`")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


async def run_suite(suite_name: str):
    _, check_fn = SUITES[suite_name]
    cases = load_cases(suite_name)
    result = await check_fn(cases)
    report_path = write_report(suite_name, result)
    return result, report_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "suites", nargs="*",
        help=f"Suite name(s) to run (default: all). Choices: {', '.join(SUITES)}",
    )
    args = parser.parse_args()

    suite_names = args.suites or list(SUITES)
    unknown = [s for s in suite_names if s not in SUITES]
    if unknown:
        print(f"Unknown suite(s): {unknown}. Choices: {list(SUITES)}", file=sys.stderr)
        return 2

    overall_ok = True
    for name in suite_names:
        print(f"Running suite: {name} ...")
        result, report_path = asyncio.run(run_suite(name))
        if result.get("skipped"):
            status = "SKIPPED"
        else:
            status = "PASS" if result["passed"] else "FAIL"
            overall_ok = overall_ok and result["passed"]
        print(f"  {status} - report: {report_path}")
        for k, v in result.get("metrics", {}).items():
            print(f"    {k}: {_fmt(v)}")

    return 0 if overall_ok else 1


if __name__ == "__main__":
    sys.exit(main())
