import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from db import async_session
from models import Event, EventStatus
from tests.conftest import TEST_PREFIX
from worker.main import MAX_ATTEMPTS, handle_event, process_message


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


def _fake_message(event_id):
    message = MagicMock()
    message.body = json.dumps({"event_id": str(event_id)}).encode()
    message.ack = AsyncMock()
    message.reject = AsyncMock()
    return message


async def test_process_message_acks_when_event_handled():
    event_id = uuid.uuid4()
    message = _fake_message(event_id)

    with patch("worker.main.handle_event", new=AsyncMock(return_value=True)) as handle:
        await process_message(message)

    handle.assert_awaited_once_with(event_id)
    message.ack.assert_awaited_once()
    message.reject.assert_not_awaited()


async def test_process_message_rejects_to_dlq_when_handling_failed():
    message = _fake_message(uuid.uuid4())

    with patch("worker.main.handle_event", new=AsyncMock(return_value=False)):
        await process_message(message)

    message.reject.assert_awaited_once_with(requeue=False)
    message.ack.assert_not_awaited()
