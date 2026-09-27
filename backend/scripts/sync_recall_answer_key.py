"""Sync the MCQ answer key for lesson recall_questions into backend/app/data/.

WHY THIS EXISTS: lesson content (content/roadmaps/**/*.json, including each
recall_questions item's `options` and which one is `correct`) is fetched
directly by the frontend from its own static bundle — the backend has ZERO
read access to it (Render's backend service deploys with root=backend/, so
the sibling content/ dir is outside the Docker build context; same
constraint sync_career_templates.py documents for career templates). Quiz v2
Quick mode needs the SERVER to independently verify which option was correct
when a lesson-card MCQ is submitted to /complete — "never trust a client
`correct: true`" (docs/IMPLEMENTATION-quiz-capture-v2.md Step 5.3) is not
enforceable for lesson cards without this. This script is that bridge:
extract just the one bit of ground truth the server needs (which option index
is correct — never the question text, options, or `why`, which stay
frontend-only) and check the resulting manifest into backend/app/data/, the
same manual "run by hand, before deploying, whenever content changes" pattern
as sync_career_templates.py.

A question's key is `<roadmap>/<slug>#<index>` — its position in that lesson's
recall_questions array. Stable in practice because content/PROMPT-recall-v2.md
authoring rules only ever APPEND items, never reorder or delete them.

Run from backend/ (no venv-specific deps beyond stdlib):
    python scripts/sync_recall_answer_key.py
"""
import json
from pathlib import Path

CONTENT_ROOT = Path(__file__).resolve().parent.parent.parent / "content" / "roadmaps"
DST = Path(__file__).resolve().parent.parent / "app" / "data" / "recall_answer_key.json"


def build_manifest() -> dict:
    manifest = {}
    skipped_ambiguous = 0

    for path in sorted(CONTENT_ROOT.glob("*/*.json")):
        if path.name.startswith("_"):
            continue
        try:
            lesson = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue

        roadmap = lesson.get("roadmap") or path.parent.name
        slug = lesson.get("slug") or path.stem
        recall_questions = lesson.get("recall_questions")
        if not isinstance(recall_questions, list):
            continue

        for i, q in enumerate(recall_questions):
            if not isinstance(q, dict) or q.get("format") != "mcq":
                continue
            options = q.get("options")
            if not isinstance(options, list):
                continue
            correct_indices = [j for j, o in enumerate(options) if isinstance(o, dict) and o.get("correct") is True]
            if len(correct_indices) != 1:
                # Malformed (content/validate.py should already catch this) — never
                # guess; a card with no answer key entry just falls back to typed
                # mode server-side rather than risk verifying against a wrong index.
                skipped_ambiguous += 1
                continue
            key = f"{roadmap}/{slug}#{i}"
            manifest[key] = {"correct_index": correct_indices[0], "options_count": len(options)}

    if skipped_ambiguous:
        print(f"Skipped {skipped_ambiguous} malformed MCQ item(s) (not exactly one correct option) — run content/validate.py to find them.")
    return manifest


def main() -> None:
    manifest = build_manifest()
    DST.parent.mkdir(parents=True, exist_ok=True)
    DST.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Synced {len(manifest)} MCQ answer key(s) from {CONTENT_ROOT} to {DST}.")


if __name__ == "__main__":
    main()
