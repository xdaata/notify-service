import uuid
from unittest.mock import AsyncMock, patch
from db import async_session
from models import Event, EventStatus
from tests.conftest import TEST_PREFIX
from worker.main import MAX_ATTEMPTS, handle_event


async def _create_test_event():
    async with async_session() as session:
        event = Event(
            event_type="user_registered",
            payload={"user_id": 1},
            idempotency_key=f"{TEST_PREFIX}{uuid.uuid4()}",
        )
        session.add(event)
        await session.commit()
        await session.refresh(event)
        return event.id


async def _get_event(event_id):
    async with async_session() as session:
        return await session.get(Event, event_id)


async def test_handle_event_marks_sent_on_success():
    event_id = await _create_test_event()
    mock_send = AsyncMock()

    with patch("worker.main.send_telegram_notification", new=mock_send):
        ok = await handle_event(event_id)

    event = await _get_event(event_id)
    assert ok is True
    assert event.status == EventStatus.SENT
    assert event.error_message is None
    mock_send.assert_awaited_once()


async def test_handle_event_retries_then_succeeds():
    event_id = await _create_test_event()
    mock_send = AsyncMock(side_effect=[Exception("boom"), Exception("boom"), None])

    with patch("worker.main.send_telegram_notification", new=mock_send), patch(
            "worker.main.BASE_DELAY", 0
    ):
        ok = await handle_event(event_id)

    event = await _get_event(event_id)
    assert ok is True
    assert event.status == EventStatus.SENT
    assert event.error_message is None
    assert mock_send.await_count == 3


async def test_handle_event_fails_after_max_attempts():
    event_id = await _create_test_event()
    mock_send = AsyncMock(side_effect=Exception("telegram is down"))

    with patch("worker.main.send_telegram_notification", new=mock_send), patch(
            "worker.main.BASE_DELAY", 0
    ):
        ok = await handle_event(event_id)

    event = await _get_event(event_id)
    assert ok is False
    assert event.status == EventStatus.FAILED
    assert "telegram is down" in event.error_message
    assert mock_send.await_count == MAX_ATTEMPTS


async def test_handle_event_skips_unknown_id():
    assert await handle_event(uuid.uuid4()) is True
