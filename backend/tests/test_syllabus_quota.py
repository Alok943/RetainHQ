"""
Lifetime personal-roadmap quota: 3 commits per user EVER — the counter is
claimed atomically on commit and never refunded, so deleting a roadmap must
not reopen the quota.
"""
from tests.conftest import USER_A, USER_B

DRAFT = {
    "title": "Operating Systems",
    "description": "Sem 5 core",
    "units": [
        {
            "title": "Unit I",
            "topics": [{"title": "Define a process", "description": "PCB, states"}],
        }
    ],
}


async def _commit(client):
    return await client.post("/api/syllabus/commit", json=DRAFT)


async def test_lifetime_cap_blocks_fourth_commit(client):
    for i in range(3):
        resp = await _commit(client)
        assert resp.status_code == 201, resp.text

    fourth = await _commit(client)
    assert fourth.status_code == 403
    assert "lifetime" in fourth.json()["detail"].lower()


async def test_delete_does_not_refund_quota(client):
    ids = []
    for _ in range(3):
        resp = await _commit(client)
        assert resp.status_code == 201
        ids.append(resp.json()["roadmap_id"])

    # Delete one — quota must stay spent.
    resp = await client.delete(f"/api/syllabus/{ids[0]}")
    assert resp.status_code == 204

    again = await _commit(client)
    assert again.status_code == 403


async def test_quota_endpoint_tracks_usage(client, as_user):
    quota = (await client.get("/api/syllabus/quota")).json()
    assert quota == {"used": 0, "limit": 3, "remaining": 3}

    await _commit(client)
    quota = (await client.get("/api/syllabus/quota")).json()
    assert quota == {"used": 1, "limit": 3, "remaining": 2}

    # Another user's quota is untouched.
    as_user(USER_B)
    quota = (await client.get("/api/syllabus/quota")).json()
    assert quota["used"] == 0
