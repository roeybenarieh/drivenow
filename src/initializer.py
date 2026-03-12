import asyncio

from src import telemetry
from src.adapters.dependency_injection import AppContainer
from src.adapters.fastapi.utils import serve_fastapi, app_factory
from src.adapters.postgres.utils import create_tables
from src.adapters.rabbitmq.utils import serve_rabbitmq


async def _run_app(container: AppContainer) -> None:
    app_config = container.config()

    # database related
    engine = container.engine()
    await create_tables(engine)
    telemetry.instrument_sqlalchemy(engine=engine.sync_engine)

    # inbound adapters tasks
    tasks = []
    if app_config.rabbitmq:
        tasks.append(asyncio.create_task(serve_rabbitmq(app_config.rabbitmq)))
    if app_config.fastAPI:
        app = app_factory()
        tasks.append(asyncio.create_task(serve_fastapi(app, app_config.fastAPI)))
        telemetry.instrument_fastapi(app)

    await asyncio.gather(*tasks)


def initialize() -> None:
    container = AppContainer()
    container.logger()  # applies dictConfig before the event loop starts
    container.meter()
    container.init_resources()
    asyncio.run(_run_app(container))
    container.shutdown_resources()
