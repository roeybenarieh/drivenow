import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from uuid import UUID


class InvalidCarDetailsError(ValueError):
    """Raised when a Car is instantiated with invalid field values."""


class InvalidRentalDetailsError(ValueError):
    """Raised when a Rental is instantiated with invalid field values."""


class CarStatus(StrEnum):
    AVAILABLE = "available"
    IN_USE = "in-use"
    UNDER_MAINTENANCE = "under-maintenance"


_TRANSITIONS: dict[CarStatus | None, set[CarStatus]] = {
    CarStatus.AVAILABLE: {CarStatus.IN_USE, CarStatus.UNDER_MAINTENANCE},
    CarStatus.IN_USE: {CarStatus.AVAILABLE},
    CarStatus.UNDER_MAINTENANCE: {CarStatus.AVAILABLE},
    None: {CarStatus.AVAILABLE},
}


@dataclass(kw_only=True)
class Entity:
    id: UUID = field(default_factory=uuid.uuid4)


@dataclass(kw_only=True)
class Car(Entity):
    model: str
    year: int
    status: CarStatus

    def __setattr__(self, name: str, value: object) -> None:
        match name:
            case "model" if not value:
                raise InvalidCarDetailsError("car model must not be empty string")
            case "year" if isinstance(value, int) and value < 1885:
                raise InvalidCarDetailsError("car year too old")
            case "status":
                if value not in CarStatus:
                    raise InvalidCarDetailsError("invalid car status")
                current = self.__dict__.get("status")
                if value not in _TRANSITIONS.get(current, []):
                    raise InvalidCarDetailsError(f"cannot transition from {current!r} to {value!r}")
        super().__setattr__(name, value)


@dataclass(kw_only=True)
class Rental(Entity):
    car_id: UUID
    customer_name: str
    start_date: datetime
    end_date: datetime

    def __post_init__(self):
        """
        Raises:
            InvalidRentalDetailsError: If customer_name is an empty string or end_date is not after start_date.
        """
        if not self.customer_name:
            raise InvalidRentalDetailsError("customer_name must not be empty string")
        if self.end_date <= self.start_date:
            raise InvalidRentalDetailsError("end_date must be after start_date")
