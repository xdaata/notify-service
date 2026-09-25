import json
import uuid

import aio_pika

from messaging.broker import QUEUE_NAME, get_channel


async def publish_event(event_id: uuid.UUID) -> None:
    channel = await get_channel()
    message = aio_pika.Message(
        body=json.dumps({"event_id": str(event_id)}).encode(),
        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
    )
    await channel.default_exchange.publish(message, routing_key=QUEUE_NAME)
