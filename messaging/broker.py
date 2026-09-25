import aio_pika

from config import settings

QUEUE_NAME = "notifications"


async def get_channel() -> aio_pika.abc.AbstractChannel:
    # новое соединение на каждый вызов, впоследствии будет пул
    connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    channel = await connection.channel()
    await channel.declare_queue(QUEUE_NAME, durable=True)
    return channel