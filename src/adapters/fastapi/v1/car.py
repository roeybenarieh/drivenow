from dependency_injector.wiring import inject, Provide
from fastapi import APIRouter, Depends, HTTPException
from pydantic import UUID4, ValidationError

from src.adapters.dependency_injection import AppContainer
from src.application.commands import CreateCarCommand, UpdateCarBody, UpdateCarCommand
from src.application.use_cases import CarUseCases, CarInUseError, CarNotAvailable
from src.domain.models import Car, CarStatus, InvalidCarDetailsError
from src.domain.ports import EntityNotFoundError

router = APIRouter(prefix="/cars", tags=["cars"])


@router.post("/", response_model=Car, status_code=201, responses={
    422: {"description": "Car details are invalid"},
})
@inject
async def create_car_route(
        body: CreateCarCommand,
        car_use_cases: CarUseCases = Depends(Provide[AppContainer.car_use_cases]),
):
    try:
        return await car_use_cases.save_car(body)
    except InvalidCarDetailsError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/", response_model=list[Car])
@inject
async def get_cars_route(
        status: CarStatus | None = None,
        car_use_cases: CarUseCases = Depends(Provide[AppContainer.car_use_cases]),
):
    return await car_use_cases.get_cars_by_status(status)


@router.get("/{car_id}", response_model=Car, responses={
    404: {"description": "Car not found"},
})
@inject
async def get_car_route(
        car_id: UUID4,
        car_use_cases: CarUseCases = Depends(Provide[AppContainer.car_use_cases]),
):
    try:
        return await car_use_cases.get_car(car_id)
    except EntityNotFoundError:
        raise HTTPException(status_code=404, detail="Car not found")


@router.patch("/{car_id}", response_model=Car, responses={
    404: {"description": "Car not found"},
    409: {"description": "Car is currently in use"},
    422: {"description": "No fields provided for update / Car details are invalid"},
})
@inject
async def update_car_route(
        car_id: UUID4,
        body: UpdateCarBody,
        car_use_cases: CarUseCases = Depends(Provide[AppContainer.car_use_cases]),
):
    try:
        cmd = UpdateCarCommand(car_id=car_id, **body.model_dump(exclude_none=True))
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors())
    try:
        return await car_use_cases.update_car(cmd)
    except EntityNotFoundError:
        raise HTTPException(status_code=404, detail="Car not found")
    except CarInUseError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except InvalidCarDetailsError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.delete("/{car_id}", status_code=204, responses={
    404: {"description": "Car not found"},
    409: {"description": "Car is not available for deletion"},
})
@inject
async def delete_car_route(
        car_id: UUID4,
        car_use_cases: CarUseCases = Depends(Provide[AppContainer.car_use_cases]),
):
    try:
        await car_use_cases.delete_car(car_id)
    except EntityNotFoundError:
        raise HTTPException(status_code=404, detail="Car not found")
    except CarNotAvailable:
        raise HTTPException(status_code=409, detail="Car can only be deleted when available")
