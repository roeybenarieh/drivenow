from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from src.domain.models import Entity


class EntityNotFoundError(Exception):
    """Error raised when an entity cannot be found in a repository"""

    def __init__(self, entity_id: UUID) -> None:
        self.entity_id = entity_id
        super().__init__(str(entity_id))


class IBaseEntityRepository[EntityT: Entity](ABC):
    @abstractmethod
    async def find_one(self, uuid: UUID) -> EntityT:
        """
        :param uuid:
        :return:
        :raises EntityNotFoundError:
        """

    @abstractmethod
    async def find_one_locked(self, uuid: UUID) -> EntityT:
        """Fetch a single entity and acquire a row-level lock (SELECT … FOR UPDATE).

        Use this inside a Unit of Work when a subsequent write depends on the
        entity's current state and concurrent modifications must be prevented
        (e.g. preventing double-booking a car).

        :param uuid:
        :return:
        :raises EntityNotFoundError:
        """

    @abstractmethod
    async def find_many(self) -> list[EntityT]: ...

    @abstractmethod
    async def save(self, entity: EntityT): ...

    @abstractmethod
    async def delete(self, entity_id: UUID): ...

    @abstractmethod
    async def patch(self, entity_id: UUID, data: dict[str, Any]): ...
