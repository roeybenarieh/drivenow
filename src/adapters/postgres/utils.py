from contextlib import contextmanager
from typing import Generator

from sqlalchemy import make_url
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine

from .tables import registry


async def create_tables(engine):
    async with engine.begin() as conn:
        await conn.run_sync(registry.metadata.create_all)


@contextmanager
def get_engine(url: str) -> Generator[AsyncEngine, None, None]:
    # since the engine is async, change driver to use psycopg
    url = make_url(url).set(drivername="postgresql+psycopg")
    engine = create_async_engine(url)
    yield engine
    engine.sync_engine.dispose()
