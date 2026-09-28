import aio_pika
from config import settings

QUEUE_NAME = "notifications"
DLQ_NAME = "notifications.dlq"


async def declare_queues(channel: aio_pika.abc.AbstractChannel) -> aio_pika.abc.AbstractQueue:
    await channel.declare_queue(DLQ_NAME, durable=True)
    return await channel.declare_queue(
        QUEUE_NAME,
        durable=True,
        arguments={
            "x-dead-letter-exchange": "",
            "x-dead-letter-routing-key": DLQ_NAME,
        },
    )


async def get_channel() -> aio_pika.abc.AbstractChannel:
    # новое соединение на каждый вызов, потом сделаем пул
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    channel = await connection.channel()
    await declare_queues(channel)
    return channel
