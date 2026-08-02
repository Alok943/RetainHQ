"""
Question-set persistence tests: a generated set must be REUSED for
QUESTION_SET_REUSE review sessions (served shuffled), then regenerated;
grading must inject the stored reference answers server-side.

The LLM generator/grader are stubbed — these tests cover the persistence and
reuse logic in the route, not Groq.
"""
import uuid

import pytest

from app.core.config import settings
from app.api.routes import reviews as reviews_module
from app.services.grader import QuestionItem
from tests.conftest import USER_A, USER_B

ACTIVITY_PAYLOAD = {
    "topic": "LRU page replacement",
    "difficulty": 3,
    "needed_hint": False,
    "key_memory": "Evict the page unused for the longest time; approximates optimal.",
}


@pytest.fixture
def grader_on(monkeypatch):
    monkeypatch.setattr(settings, "GRADER_ENABLED", True)


@pytest.fixture
def fake_generator(monkeypatch):
    """Stub the LLM generator; records call count so reuse is observable."""
    calls = {"n": 0}

    async def _fake(topic, depth="main", **kwargs):
        calls["n"] += 1
        n = 5 if depth == "deep" else 3
        return [
            QuestionItem(
                question=f"[{depth} gen{calls['n']}] Q{i}?",
                reference_answer=f"Reference answer {i}.",
            )
            for i in range(1, n + 1)
        ]

    monkeypatch.setattr(reviews_module, "generate_question_items", _fake)
    return calls


async def _due_review_id(client) -> str:
    resp = await client.post("/api/activities/", json=ACTIVITY_PAYLOAD)
    assert resp.status_code == 200, resp.text
    return (await client.get("/api/reviews/due")).json()[0]["id"]


async def test_question_set_is_reused_then_regenerated(client, grader_on, fake_generator):
    review_id = await _due_review_id(client)

    # Session 1: generates a set.
    first = await client.post(f"/api/reviews/{review_id}/questions", json={"depth": "main"})
    assert first.status_code == 200, first.text
    assert fake_generator["n"] == 1
    q1 = first.json()["questions"]
    assert len(q1) == 3

    # Session 2: SAME set served again (no new generation), same questions.
    second = await client.post(f"/api/reviews/{review_id}/questions", json={"depth": "main"})
    assert second.status_code == 200
    assert fake_generator["n"] == 1  # reused, not regenerated
    assert sorted(second.json()["questions"]) == sorted(q1)

    # Session 3: reuse budget (QUESTION_SET_REUSE=2) exhausted → fresh set.
    third = await client.post(f"/api/reviews/{review_id}/questions", json={"depth": "main"})
    assert third.status_code == 200
    assert fake_generator["n"] == 2
    assert sorted(third.json()["questions"]) != sorted(q1)


async def test_depths_get_separate_sets(client, grader_on, fake_generator):
    review_id = await _due_review_id(client)

    main = await client.post(f"/api/reviews/{review_id}/questions", json={"depth": "main"})
    deep = await client.post(f"/api/reviews/{review_id}/questions", json={"depth": "deep"})
    assert len(main.json()["questions"]) == 3
    assert len(deep.json()["questions"]) == 5
    assert fake_generator["n"] == 2  # one set per depth

    # No body at all defaults to main and reuses the main set.
    default = await client.post(f"/api/reviews/{review_id}/questions")
    assert default.status_code == 200
    assert fake_generator["n"] == 2


async def test_questions_are_scoped_to_owner(client, as_user, grader_on, fake_generator):
    review_id = await _due_review_id(client)
    as_user(USER_B)
    resp = await client.post(f"/api/reviews/{review_id}/questions", json={"depth": "main"})
    assert resp.status_code == 404  # B must not pull questions for A's review


async def test_grading_injects_stored_reference_answers(client, grader_on, fake_generator, monkeypatch):
    review_id = await _due_review_id(client)
    questions = (
        await client.post(f"/api/reviews/{review_id}/questions", json={"depth": "main"})
    ).json()["questions"]

    seen = {}

    async def _fake_grade(topic, key_memory, qa_pairs):
        seen["pairs"] = qa_pairs
        from app.services.grader import QuestionSetGrade, QuestionItemGrade
        return QuestionSetGrade(
            recalled=True,
            feedback="ok",
            items=[QuestionItemGrade(question=p["question"], correct=True, note="ok") for p in qa_pairs],
        )

    monkeypatch.setattr(reviews_module, "grade_question_set", _fake_grade)

    resp = await client.post(
        f"/api/reviews/{review_id}/grade-questions",
        json={"answers": [{"question": q, "answer": "my attempt"} for q in questions]},
    )
    assert resp.status_code == 200, resp.text
    # Every pair must carry the stored (server-side) reference answer.
    assert all(p.get("reference_answer") for p in seen["pairs"])


# --------------------------------------------------------------------------- #
# Prompt assembly: the student's approach must reach the model as its own block.
# Asserting on the constructed user message is the only way to catch a silent
# regression here — a dropped block still produces perfectly plausible questions,
# just about the textbook solution instead of the user's code.
# --------------------------------------------------------------------------- #

async def test_user_approach_block_is_sent_to_the_model(monkeypatch):
    from app.services import grader as grader_module

    seen = {}

    async def fake_call(system_prompt, user_msg, **kwargs):
        seen["system"] = system_prompt
        seen["user"] = user_msg
        return '{"questions": [{"question": "Q?", "reference_answer": "A."}]}'

    monkeypatch.setattr(grader_module, "_grader_json", fake_call)

    await grader_module.generate_question_items(
        topic="LeetCode 567: Permutation in String",
        depth="main",
        key_memory="Fixed window, compare frequencies.",
        node_title="Sliding window (fixed)",
        node_description="A fixed-size window sliding across the array.",
        problem_context={
            "problem_title": "Permutation in String",
            "primary_node_title": "Sliding window (fixed)",
            "alternative_node_titles": [],
            "language": "python",
            "user_approach_title": "Sliding window (fixed)",
            "user_approach_facts": [
                "Compares two dicts for equality on every slide, O(k) per step.",
                "Deletes zero-count keys so dict equality stays valid.",
            ],
        },
    )

    msg = seen["user"]
    assert "THE STUDENT'S APPROACH" in msg
    assert "Compares two dicts for equality on every slide" in msg
    assert "Deletes zero-count keys" in msg
    # And the rule that makes the block binding.
    assert "overrides the canonical" in seen["system"]


async def test_no_approach_block_when_the_user_shared_no_code(monkeypatch):
    from app.services import grader as grader_module

    seen = {}

    async def fake_call(system_prompt, user_msg, **kwargs):
        seen["user"] = user_msg
        return '{"questions": [{"question": "Q?", "reference_answer": "A."}]}'

    monkeypatch.setattr(grader_module, "_grader_json", fake_call)

    await grader_module.generate_question_items(
        topic="LeetCode 1: Two Sum",
        depth="main",
        key_memory="Hash map of complements.",
        node_title="Hash Tables",
        problem_context={
            "problem_title": "Two Sum",
            "primary_node_title": "Hash Tables",
            "alternative_node_titles": [],
            "language": "python",
            "user_approach_title": None,
            "user_approach_facts": [],
        },
    )

    assert "PROBLEM CONTEXT" in seen["user"]
    assert "THE STUDENT'S APPROACH" not in seen["user"]
