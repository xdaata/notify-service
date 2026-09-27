import asyncio
import json
import uuid
import aio_pika
from config import settings
from db import async_session
from messaging.broker import QUEUE_NAME
from models import Event, EventStatus
from worker.notifier import send_telegram_notification


async def handle_event(event_id: uuid.UUID) -> None:
    async with async_session() as session:
        event = await session.get(Event, event_id)
        if event is None:
            return

        event.status = EventStatus.PROCESSING
        await session.commit()

        try:
            text = f"{event.event_type}: {event.payload}"
            await send_telegram_notification(text)
            event.status = EventStatus.SENT
        except Exception as exc:
            # без ретраев пока - просто фиксируем факт и причину провала
            event.status = EventStatus.FAILED
            event.error_message = str(exc)
            print(f"failed to send notification for {event_id}: {exc}")

        await session.commit()


async def process_message(message: aio_pika.abc.AbstractIncomingMessage) -> None:
    async with message.process():
        data = json.loads(message.body)
        event_id = uuid.UUID(data["event_id"])
        await handle_event(event_id)


async def main() -> None:
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=10)
        queue = await channel.declare_queue(QUEUE_NAME, durable=True)

        print(f"worker started, listening on '{QUEUE_NAME}'")
        await queue.consume(process_message)
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
