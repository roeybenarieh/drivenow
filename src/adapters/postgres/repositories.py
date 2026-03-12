from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import QueryableAttribute

from src.domain.models import Car, Rental, Entity
from src.domain.ports import IBaseEntityRepository, EntityNotFoundError


class Queryable[T](QueryableAttribute):
    """Generic class for all objects that can be used in sqlalchemy query."""


class PostgresRepository[EntityT: Entity](IBaseEntityRepository[EntityT]):
    entity: type[Queryable[EntityT]]

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_one(self, entity_id: UUID) -> EntityT:
        stmt = select(self.entity).where(self.entity.id == entity_id)
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        if row is None:
            raise EntityNotFoundError(entity_id)
        return row

    async def find_one_locked(self, entity_id: UUID) -> EntityT:
        stmt = select(self.entity).where(self.entity.id == entity_id).with_for_update()
        row = (await self._session.execute(stmt)).scalar_one_or_none()
        if row is None:
            raise EntityNotFoundError(entity_id)
        return row

    async def find_many(self) -> list[EntityT]:
        rows = (await self._session.execute(select(self.entity))).scalars().all()
        return list(rows)

    async def save(self, entity: EntityT) -> None:
        await self._session.merge(entity)

    async def delete(self, entity_id: UUID) -> None:
        row = await self._session.get(self.entity, entity_id)
        if row:
            await self._session.delete(row)

    async def patch(self, entity_id: UUID, data: dict[str, Any]) -> None:
        row = await self._session.get(self.entity, entity_id)
        if row is None:
            raise EntityNotFoundError(entity_id)
        for k, v in data.items():
            setattr(row, k, v)


class PostgresCarRepository(PostgresRepository[Car]):
    entity = Car


class PostgresRentalRepository(PostgresRepository[Rental]):
    entity = Rental
