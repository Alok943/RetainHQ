"""Sync career-tree role templates from content/career-templates/ into
backend/app/data/career_templates/.

WHY THIS EXISTS: content/career-templates/<role>.v<N>.json is the canonical
authoring + CI-validated location (SPEC-career-coach-phase2.md §3.1,
content/validate_career_templates.py) — same convention as every other
content file. But Render's backend service deploys with root=backend/ (see
docs/SYSTEM-OVERVIEW.md §1), so the Docker build context never includes the
sibling content/ directory; services/career_tree.py can only read files that
actually ship inside the backend/ package. This script is the (manual, not
automated per-deploy) bridge between the two — analogous to
frontend/sync-content.mjs, which does the same job for the frontend build via
a predev/prebuild hook. No such hook exists on the backend today, so: run
this by hand whenever a template under content/career-templates/ changes,
before deploying.

Run from backend/:
    ./.venv/Scripts/python.exe sync_career_templates.py
"""
import shutil
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "content" / "career-templates"
DST = Path(__file__).resolve().parent / "app" / "data" / "career_templates"


def main() -> None:
    DST.mkdir(parents=True, exist_ok=True)
    copied = 0
    for src_file in sorted(SRC.glob("*.json")):
        shutil.copyfile(src_file, DST / src_file.name)
        copied += 1
    print(f"Synced {copied} template(s) from {SRC} to {DST}.")


if __name__ == "__main__":
    main()
