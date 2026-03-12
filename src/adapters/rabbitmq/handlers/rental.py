import logging

from dependency_injector.wiring import inject, Provide
from opentelemetry.metrics import Counter
from pydantic import ValidationError

from src.adapters.dependency_injection import AppContainer
from src.application.commands import CreateRentalCommand, EndRentalCommand
from src.application.use_cases import RentalUseCases
from src.domain.models import InvalidCarDetailsError, InvalidRentalDetailsError
from src.domain.ports import EntityNotFoundError


@inject
async def handle_rental_register(
        body: dict,
        rental_use_cases: RentalUseCases = Provide[AppContainer.rental_use_cases],
        logger: logging.Logger = Provide[AppContainer.logger],
        errors: Counter = Provide[AppContainer.rabbitmq_rental_errors],
) -> None:
    try:
        cmd = CreateRentalCommand.model_validate(body)
    except ValidationError as e:
        logger.warning("rental.register: invalid payload: %s", e)
        errors.add(1, {"operation": "register", "reason": "validation_error"})
        return
    try:
        await rental_use_cases.register_new_rental(cmd)
    except EntityNotFoundError:
        logger.warning("rental.register: car not found: %s", cmd.car_id)
        errors.add(1, {"operation": "register", "reason": "not_found"})
    except InvalidCarDetailsError:
        logger.warning("rental.register: car not available: %s", cmd.car_id)
        errors.add(1, {"operation": "register", "reason": "conflict"})
    except InvalidRentalDetailsError as e:
        logger.warning("rental.register: invalid rental details: %s", e)
        errors.add(1, {"operation": "register", "reason": "validation_error"})


@inject
async def handle_rental_end(
        body: dict,
        rental_use_cases: RentalUseCases = Provide[AppContainer.rental_use_cases],
        logger: logging.Logger = Provide[AppContainer.logger],
        errors: Counter = Provide[AppContainer.rabbitmq_rental_errors],
) -> None:
    try:
        cmd = EndRentalCommand.model_validate(body)
    except ValidationError as e:
        logger.warning("rental.end: invalid payload: %s", e)
        errors.add(1, {"operation": "end", "reason": "missing_field"})
        return
    try:
        await rental_use_cases.end_rental(cmd.rental_id)
    except EntityNotFoundError as e:
        if e.entity_id == cmd.rental_id:
            logger.warning("rental.end: rental not found: %s", cmd.rental_id)
            errors.add(1, {"operation": "end", "reason": "not_found"})
        else:
            logger.error("rental.end: data integrity error — car linked to rental no longer exists, rental_id=%s",
                         cmd.rental_id)
            errors.add(1, {"operation": "end", "reason": "internal_error"})
