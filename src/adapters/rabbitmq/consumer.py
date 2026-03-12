import asyncio
import json
import logging
import time
from collections.abc import Callable, Coroutine
from typing import Any

from aio_pika.abc import AbstractIncomingMessage
from dependency_injector.wiring import inject, Provide
from opentelemetry.metrics import Meter

from src.adapters.dependency_injection import AppContainer
from .handlers import car, rental

_HANDLERS: dict[str, Callable[[dict], Coroutine[Any, Any, None]]] = {
    "car.create": car.handle_car_create,
    "car.update": car.handle_car_update,
    "car.delete": car.handle_car_delete,
    "rental.register": rental.handle_rental_register,
    "rental.end": rental.handle_rental_end,
}


@inject
def make_callback(
        meter: Meter = Provide[AppContainer.meter],
        logger: logging.Logger = Provide[AppContainer.logger],
) -> Callable[[AbstractIncomingMessage], Coroutine[Any, Any, None]]:
    """Return an async message callback that dispatches by routing key."""
    processing_duration = meter.create_histogram(
        name="rabbitmq.message.processing_duration",
        description="Time to process a single RabbitMQ message",
        unit="s",
    )

    async def callback(message: AbstractIncomingMessage) -> None:
        routing_key = message.routing_key or ""
        start = time.monotonic()
        async with message.process():
            handler = _HANDLERS.get(routing_key)
            if handler is None:
                logger.warning(f"No handler for routing key {routing_key} — discarding")
                return

            try:
                body = json.loads(message.body)
            except json.JSONDecodeError:
                logger.warning(f"Received non-JSON message on routing key {routing_key} — discarding")
                return

            # Run the handler as a task so messages are processed concurrently
            # (aio-pika with prefetch_count > 1 already dispatches concurrently,
            # but wrapping in a task prevents a slow handler from blocking ack).
            await asyncio.create_task(handler(body))
        processing_duration.record(
            time.monotonic() - start,
            attributes={"routing_key": routing_key},
        )

    return callback
