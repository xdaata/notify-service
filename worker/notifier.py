import httpx

from config import settings


async def send_telegram_notification(text: str) -> None:
    url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url, json={"chat_id": settings.telegram_chat_id, "text": text}
        )
        response.raise_for_status()
