import asyncio
import logging
from uuid import UUID

from opentelemetry.metrics import Meter

from src.application.commands import CreateCarCommand, UpdateCarCommand, CreateRentalCommand
from src.domain.models import Car, CarStatus, InvalidCarDetailsError, Rental
from src.domain.ports import UnitOfWork
from src.domain.service import RentalService


class CarInUseError(Exception):
    """Exception raised when an action can't perform because the car is in use."""


class CarNotAvailable(Exception):
    """Exception raised when an action can't perform because the car is not available."""


class CarUseCases:
    def __init__(self, uow: UnitOfWork, logger: logging.Logger, meter: Meter) -> None:
        self._uow = uow
        self._logger = logger
        self._active_cars = meter.create_up_down_counter(
            name="drivenow.cars.active",
            description="Currently active cars"
        )

    async def save_car(self, cmd: CreateCarCommand) -> Car:
        """
        Raises:
            InvalidCarDetailsError: If model is empty or year is before 1885.
        """
        car = Car(model=cmd.model, year=cmd.year, status=CarStatus.AVAILABLE)
        async with self._uow as uow:
            await uow.car_repository.save(car)
            await uow.commit()
        self._logger.info(f"New Car created with id={car.id}")
        self._active_cars.add(1)
        return car

    async def get_cars_by_status(self, status: CarStatus | None = None) -> list[Car]:
        async with self._uow as uow:
            cars = await uow.car_repository.find_many()
        if status is not None:
            cars = [c for c in cars if c.status == status]
        return cars

    async def get_car(self, car_id: UUID) -> Car:
        """
        Raises:
            EntityNotFoundError: If no car with car_id exists.
        """
        async with self._uow as uow:
            return await uow.car_repository.find_one(car_id)

    async def update_car(self, cmd: UpdateCarCommand) -> Car:
        """
        Raises:
            EntityNotFoundError: If no car with car_id exists.
            InvalidCarDetailsError: If the patched values are not valid.
        """
        fields = cmd.model_dump(exclude_none=True, exclude={"car_id"})
        async with self._uow as uow:
            car = await uow.car_repository.find_one_locked(cmd.car_id)

            if car.status == CarStatus.IN_USE:
                raise CarInUseError("Car is in use, cannot manually change status")
            if cmd.status is CarStatus.IN_USE:
                raise InvalidCarDetailsError("Car can become used only by renting it")

            for k, v in fields.items():
                setattr(car, k, v)
            await uow.car_repository.save(car)
            await uow.commit()
        self._logger.info(f"Car with id={cmd.car_id} got updated")
        return car

    async def delete_car(self, car_id: UUID) -> None:
        """
        Raises:
            EntityNotFoundError: If no car with car_id exists.
            InvalidCarDetailsError: If car is note available, meaning cannot get deleted.
        """
        async with self._uow as uow:
            car = await uow.car_repository.find_one_locked(car_id)

            if car.status != CarStatus.AVAILABLE:
                raise CarNotAvailable("cannot delete a car that is not available")

            await uow.car_repository.delete(car_id)
            await uow.commit()
        self._logger.info(f"Car with id={car_id} got deleted")
        self._active_cars.add(-1)


class RentalUseCases:
    def __init__(self, uow: UnitOfWork, logger: logging.Logger, meter: Meter, service: RentalService) -> None:
        self._uow = uow
        self._logger = logger
        self._service = service
        self._rentals_count = meter.create_up_down_counter(
            name="drivenow.rentals.registered",
            description="Rentals successfully registered"
        )

    async def register_new_rental(self, cmd: CreateRentalCommand) -> Rental:
        """
        Raises:
            EntityNotFoundError: If no car with car_id exists.
            InvalidCarDetailsError: If the car is not in AVAILABLE status.
            InvalidRentalDetailsError: If customer_name is empty or end_date is not after start_date.
        """
        async with self._uow as uow:
            car = await uow.car_repository.find_one_locked(cmd.car_id)
            rental = self._service.create_rental(car, cmd.customer_name, cmd.start_date, cmd.end_date)
            await asyncio.gather(uow.car_repository.save(car), uow.rental_repository.save(rental))
            await uow.commit()
        self._logger.info(f"New rental registered with id={rental.id} on car with id={car.id}")
        self._rentals_count.add(1)
        return rental

    async def get_rental(self, rental_id: UUID) -> Rental:
        """
        Raises:
            EntityNotFoundError: If no rental with rental_id exists.
        """
        async with self._uow as uow:
            return await uow.rental_repository.find_one(rental_id)

    async def end_rental(self, rental_id: UUID) -> None:
        """
        Raises:
            EntityNotFoundError: If no rental with rental_id exists, or the car linked to it no longer exists.
            InvalidCarDetailsError: if the car cant change state to "available".
        """
        async with self._uow as uow:
            rental = await uow.rental_repository.find_one_locked(rental_id)
            car = await uow.car_repository.find_one_locked(rental.car_id)

            car.status = CarStatus.AVAILABLE

            await asyncio.gather(
                uow.car_repository.save(car),
                uow.rental_repository.delete(rental.id)
            )
            await uow.commit()
        self._logger.info(f"Rental with id={rental_id} ended")
        self._rentals_count.add(-1)
