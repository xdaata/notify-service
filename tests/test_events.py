import uuid

from tests.conftest import TEST_PREFIX


async def test_health_returns_ok(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


async def test_create_event_returns_202_with_queued_status(client):
    key = f"{TEST_PREFIX}{uuid.uuid4()}"
    response = await client.post(
        "/events",
        json={
            "event_type": "user_registered",
            "payload": {"user_id": 1},
            "idempotency_key": key,
        },
    )
    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "queued"
    assert body["event_type"] == "user_registered"


async def test_create_event_is_idempotent(client):
    key = f"{TEST_PREFIX}{uuid.uuid4()}"
    payload = {
        "event_type": "user_registered",
        "payload": {"user_id": 1},
        "idempotency_key": key,
    }

    first = await client.post("/events", json=payload)
    second = await client.post("/events", json=payload)

    assert first.json()["id"] == second.json()["id"]


async def test_get_event_returns_created_event(client):
    key = f"{TEST_PREFIX}{uuid.uuid4()}"
    created = await client.post(
        "/events",
        json={
            "event_type": "order_paid",
            "payload": {"order_id": 42},
            "idempotency_key": key,
        },
    )
    event_id = created.json()["id"]

    response = await client.get(f"/events/{event_id}")

    assert response.status_code == 200
    assert response.json()["id"] == event_id


async def test_get_event_returns_404(client):
    random_id = uuid.uuid4()
    response = await client.get(f"/events/{random_id}")
    assert response.status_code == 404
