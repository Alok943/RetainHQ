"""
push_subscriptions: vapid-key gating, subscribe/unsubscribe round-trip, and
ownership semantics (endpoint is the upsert key, so re-subscribing the same
endpoint under a different user is an intentional device/account handoff,
not a leak — tested explicitly below).
"""
from sqlalchemy import text

from tests.conftest import USER_A, USER_B

SUB = {
    "endpoint": "https://fcm.googleapis.com/fcm/send/abc123",
    "p256dh": "p256dh-key-value",
    "auth": "auth-secret-value",
    "userAgent": "pytest-agent",
}


async def test_vapid_key_404_when_unconfigured(client):
    resp = await client.get("/api/push/vapid-public-key")
    assert resp.status_code == 404


async def test_subscribe_then_unsubscribe_round_trip(client, db, as_user):
    as_user(USER_A)
    resp = await client.post("/api/push/subscribe", json=SUB)
    assert resp.status_code == 204

    row = (await db.execute(text("select user_id, p256dh from push_subscriptions where endpoint = :e"), {"e": SUB["endpoint"]})).first()
    assert row is not None
    assert str(row[0]) == USER_A.id
    assert row[1] == "p256dh-key-value"

    resp = await client.delete("/api/push/subscribe", params={"endpoint": SUB["endpoint"]})
    assert resp.status_code == 204

    row = (await db.execute(text("select 1 from push_subscriptions where endpoint = :e"), {"e": SUB["endpoint"]})).first()
    assert row is None


async def test_unsubscribe_does_not_affect_another_users_subscription(client, db, as_user):
    as_user(USER_A)
    await client.post("/api/push/subscribe", json=SUB)

    as_user(USER_B)
    # Bob deletes an endpoint he doesn't own — no-op, not an error, and must
    # NOT remove Alice's row (the WHERE clause scopes by user_id too).
    resp = await client.delete("/api/push/subscribe", params={"endpoint": SUB["endpoint"]})
    assert resp.status_code == 204

    row = (await db.execute(text("select 1 from push_subscriptions where endpoint = :e"), {"e": SUB["endpoint"]})).first()
    assert row is not None  # Alice's subscription survives


async def test_resubscribe_same_endpoint_reassigns_owner(client, db, as_user):
    """Intentional: endpoint is the natural upsert key. A device re-subscribing
    under a different signed-in account should reassign ownership, not error —
    this is the expected account-swap-on-shared-device case."""
    as_user(USER_A)
    await client.post("/api/push/subscribe", json=SUB)

    as_user(USER_B)
    resp = await client.post("/api/push/subscribe", json=SUB)
    assert resp.status_code == 204

    row = (await db.execute(text("select user_id from push_subscriptions where endpoint = :e"), {"e": SUB["endpoint"]})).first()
    assert str(row[0]) == USER_B.id

    count = (await db.execute(text("select count(*) from push_subscriptions where endpoint = :e"), {"e": SUB["endpoint"]})).scalar_one()
    assert count == 1  # upsert, not a duplicate row
