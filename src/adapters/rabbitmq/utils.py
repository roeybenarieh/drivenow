import asyncio

import aio_pika
from aio_pika.abc import AbstractRobustConnection, AbstractRobustChannel

from src.config import RabbitMQSettings
from .consumer import make_callback


async def serve_rabbitmq(settings: RabbitMQSettings) -> None:
    """
    Connect to RabbitMQ, declare a single durable queue, consume messages until
    canceled, then close the connection.

    Incoming messages are dispatched to the appropriate handler by ``routing_key``.

    Message format (JSON body):
        Request  → {"field": value, ...}
        Response → {"success": bool, "data": ..., "error": str|null, "error_code": str|null}

    Set ``reply_to`` and ``correlation_id`` AMQP properties on the request message
    to receive a response back on the specified reply queue.
    """
    connection: AbstractRobustConnection = await aio_pika.connect_robust(settings.dsn.unicode_string())
    channel: AbstractRobustChannel = await connection.channel()

    queue = await channel.declare_queue(settings.queue_name, durable=True)
    await queue.consume(make_callback())

    try:
        await asyncio.Event().wait()
    finally:
        await connection.close()
