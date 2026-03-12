import logging

from dependency_injector.wiring import inject, Provide
from opentelemetry.metrics import Counter
from pydantic import ValidationError

from src.adapters.dependency_injection import AppContainer
from src.application.commands import (
    CreateCarCommand,
    UpdateCarCommand,
    DeleteCarCommand,
)
from src.application.use_cases import CarUseCases, CarInUseError, CarNotAvailable
from src.domain.models import InvalidCarDetailsError
from src.domain.ports import EntityNotFoundError


@inject
async def handle_car_create(
        body: dict,
        car_use_cases: CarUseCases = Provide[AppContainer.car_use_cases],
        logger: logging.Logger = Provide[AppContainer.logger],
        errors: Counter = Provide[AppContainer.rabbitmq_car_errors],
) -> None:
    try:
        cmd = CreateCarCommand.model_validate(body)
    except ValidationError as e:
        logger.warning("car.create: invalid payload: %s", e)
        errors.add(1, {"operation": "create", "reason": "validation_error"})
        return
    try:
        await car_use_cases.save_car(cmd)
    except InvalidCarDetailsError as e:
        logger.warning("car.create: validation error: %s", e)
        errors.add(1, {"operation": "create", "reason": "validation_error"})


@inject
async def handle_car_update(
        body: dict,
        car_use_cases: CarUseCases = Provide[AppContainer.car_use_cases],
        logger: logging.Logger = Provide[AppContainer.logger],
        errors: Counter = Provide[AppContainer.rabbitmq_car_errors],
) -> None:
    try:
        cmd = UpdateCarCommand.model_validate(body)
    except ValidationError as e:
        logger.warning("car.update: invalid payload: %s", e)
        errors.add(1, {"operation": "update", "reason": "validation_error"})
        return
    try:
        await car_use_cases.update_car(cmd)
    except EntityNotFoundError:
        logger.warning("car.update: car not found: %s", cmd.car_id)
        errors.add(1, {"operation": "update", "reason": "not_found"})
    except CarInUseError as e:
        logger.warning("car.update: conflict: %s", e)
        errors.add(1, {"operation": "update", "reason": "conflict"})
    except InvalidCarDetailsError as e:
        logger.warning("car.update: validation error: %s", e)
        errors.add(1, {"operation": "update", "reason": "validation_error"})


@inject
async def handle_car_delete(
        body: dict,
        car_use_cases: CarUseCases = Provide[AppContainer.car_use_cases],
        logger: logging.Logger = Provide[AppContainer.logger],
        errors: Counter = Provide[AppContainer.rabbitmq_car_errors],
) -> None:
    try:
        cmd = DeleteCarCommand.model_validate(body)
    except ValidationError as e:
        logger.warning("car.delete: invalid payload: %s", e)
        errors.add(1, {"operation": "delete", "reason": "validation_error"})
        return
    try:
        await car_use_cases.delete_car(cmd.car_id)
    except EntityNotFoundError:
        logger.warning("car.delete: car not found: %s", cmd.car_id)
        errors.add(1, {"operation": "delete", "reason": "not_found"})
    except CarNotAvailable as e:
        logger.warning("car.delete: conflict: %s", e)
        errors.add(1, {"operation": "delete", "reason": "conflict"})
