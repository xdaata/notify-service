import asyncio
import json
import uuid
import aio_pika
from config import settings
from db import async_session
from messaging.broker import QUEUE_NAME, declare_queues
from models import Event, EventStatus
from worker.notifier import send_telegram_notification

MAX_ATTEMPTS = 3
BASE_DELAY = 1


async def handle_event(event_id: uuid.UUID) -> bool:
    async with async_session() as session:
        event = await session.get(Event, event_id)
        if event is None:
            print(f"event {event_id} not found, skipping")
            return True

        event.status = EventStatus.PROCESSING
        await session.commit()

        text = f"{event.event_type}: {event.payload}"
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                await send_telegram_notification(text)
            except Exception as exc:
                event.error_message = str(exc)
                print(f"attempt {attempt}/{MAX_ATTEMPTS} failed for {event_id}: {exc}")
                if attempt < MAX_ATTEMPTS:
                    await asyncio.sleep(BASE_DELAY * 2 ** (attempt - 1))
            else:
                event.status = EventStatus.SENT
                event.error_message = None
                await session.commit()
                return True

        event.status = EventStatus.FAILED
        await session.commit()
        return False


async def process_message(message: aio_pika.abc.AbstractIncomingMessage) -> None:
    data = json.loads(message.body)
    ok = await handle_event(uuid.UUID(data["event_id"]))
    if ok:
        await message.ack()
    else:
        await message.reject(requeue=False)


async def main() -> None:
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=10)
        queue = await declare_queues(channel)

        print(f"worker started, listening on '{QUEUE_NAME}'")
        await queue.consume(process_message)
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
