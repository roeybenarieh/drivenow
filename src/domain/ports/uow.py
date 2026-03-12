from abc import ABC, abstractmethod
from typing import Self

from src.domain.models import Rental, Car
from src.domain.ports.repository import IBaseEntityRepository


class UnitOfWork(ABC):
    car_repository: IBaseEntityRepository[Car]
    rental_repository: IBaseEntityRepository[Rental]

    @abstractmethod
    async def __aenter__(self) -> Self: ...

    @abstractmethod
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None: ...

    @abstractmethod
    async def commit(self) -> None: ...

    @abstractmethod
    async def rollback(self) -> None: ...
