import json
from unittest.mock import patch
import httpx
import pytest
from config import settings
from worker.notifier import send_telegram_notification


def _mock_telegram(handler):
    real_client = httpx.AsyncClient
    transport = httpx.MockTransport(handler)
    return patch(
        "worker.notifier.httpx.AsyncClient",
        new=lambda: real_client(transport=transport),
    )


async def test_send_telegram_notification_posts_message():
    seen = []

    def handler(request):
        seen.append(request)
        return httpx.Response(200, json={"ok": True})

    with _mock_telegram(handler):
        await send_telegram_notification("hello")

    assert len(seen) == 1
    assert seen[0].url.path.endswith("/sendMessage")
    body = json.loads(seen[0].content)
    assert body["text"] == "hello"
    assert body["chat_id"] == settings.telegram_chat_id


async def test_send_telegram_notification_raises_without_leaking_token():
    with _mock_telegram(lambda request: httpx.Response(401)):
        with pytest.raises(RuntimeError) as exc_info:
            await send_telegram_notification("hello")

    assert "401" in str(exc_info.value)
    assert settings.telegram_bot_token not in str(exc_info.value)
