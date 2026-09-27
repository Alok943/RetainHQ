"""Eval harness for LLM-generated content and grading (docs/IMPLEMENTATION-quiz-capture-v2.md Step 2).

Run with `python -m evals.run [suite ...]` from `backend/`. Never imported by
the default pytest run (it calls the live model) — `tests/test_eval_datasets.py`
covers the schema-only check that IS part of `pytest`.
"""
