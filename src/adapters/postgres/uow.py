from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.domain.ports import UnitOfWork
from .repositories import PostgresCarRepository, PostgresRentalRepository


class PgUnitOfWork(UnitOfWork):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def __aenter__(self) -> Self:
        self._session = self._session_factory()
        await self._session.begin()
        self.car_repository = PostgresCarRepository(self._session)
        self.rental_repository = PostgresRentalRepository(self._session)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type:
            await self.rollback()
        await self._session.close()

    async def commit(self) -> None:
        await self._session.commit()

    async def rollback(self) -> None:
        await self._session.rollback()
