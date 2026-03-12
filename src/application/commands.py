from datetime import datetime
from typing import Annotated, Self

from pydantic import BaseModel, Field, UUID4, model_validator, ConfigDict, FutureDatetime

from src.domain.models import CarStatus

NoneEmptyString = Annotated[str, Field(min_length=1, strict=True)]


class BaseCommand(BaseModel):
    model_config = ConfigDict(extra='forbid')


class CreateCarCommand(BaseCommand):
    model: NoneEmptyString
    year: int = Field(ge=1885)


class UpdateCarBody(BaseCommand):
    model: NoneEmptyString | None = None
    year: int | None = Field(default=None, ge=1885)
    status: CarStatus | None = None


class UpdateCarCommand(UpdateCarBody):
    car_id: UUID4

    @model_validator(mode="after")
    def at_least_one_field(self) -> Self:
        if all(v is None for v in [self.model, self.year, self.status]):
            raise ValueError("At least one field must be provided for update")
        return self


class GetCarCommand(BaseCommand):
    car_id: UUID4


class DeleteCarCommand(BaseCommand):
    car_id: UUID4


class ListCarsCommand(BaseCommand):
    status: CarStatus | None = None


class CreateRentalCommand(BaseCommand):
    car_id: UUID4
    customer_name: NoneEmptyString
    start_date: datetime
    end_date: FutureDatetime


class GetRentalCommand(BaseCommand):
    rental_id: UUID4


class EndRentalCommand(BaseCommand):
    rental_id: UUID4
