import uuid
from unittest.mock import AsyncMock, patch
from db import async_session
from models import Event, EventStatus
from tests.conftest import TEST_PREFIX
from worker.main import handle_event


async def _create_test_event(event_type="user_registered", payload=None):
    async with async_session() as session:
        event = Event(
            event_type=event_type,
            payload=payload or {"user_id": 1},
            idempotency_key=f"{TEST_PREFIX}{uuid.uuid4()}",
        )
        session.add(event)
        await session.commit()
        await session.refresh(event)
        return event.id


async def test_handle_event_marks_sent_on_success():
    event_id = await _create_test_event()

    with patch("worker.main.send_telegram_notification", new=AsyncMock()):
        await handle_event(event_id)

    async with async_session() as session:
        event = await session.get(Event, event_id)
        assert event.status == EventStatus.SENT
        assert event.error_message is None


async def test_handle_event_marks_failed_on_telegram_error():
    event_id = await _create_test_event()
    mock_send = AsyncMock(side_effect=Exception("telegram is down"))

    with patch("worker.main.send_telegram_notification", new=mock_send):
        await handle_event(event_id)

    async with async_session() as session:
        event = await session.get(Event, event_id)
        assert event.status == EventStatus.FAILED
        assert "telegram is down" in event.error_message


async def test_handle_event_ignores_unknown_id():
    # просто не должно упасть - событие не найдено, и это ок
    await handle_event(uuid.uuid4())