from dependency_injector.wiring import inject, Provide
from fastapi import APIRouter, Depends, HTTPException
from pydantic import UUID4

from src.adapters.dependency_injection import AppContainer
from src.application.commands import CreateRentalCommand
from src.application.use_cases import RentalUseCases
from src.domain.models import InvalidCarDetailsError, InvalidRentalDetailsError, Rental
from src.domain.ports import EntityNotFoundError

router = APIRouter(prefix="/rentals", tags=["rentals"])


@router.post("/", response_model=Rental, status_code=201, responses={
    404: {"description": "Car not found"},
    409: {"description": "Car is not available for rental"},
    422: {"description": "Rental details violate domain rules"},
})
@inject
async def register_rental_route(
        body: CreateRentalCommand,
        rental_use_cases: RentalUseCases = Depends(Provide[AppContainer.rental_use_cases]),
):
    try:
        return await rental_use_cases.register_new_rental(body)
    except EntityNotFoundError:
        raise HTTPException(status_code=404, detail="Car not found")
    except InvalidCarDetailsError:
        raise HTTPException(status_code=409, detail="Car is not available for rental")
    except InvalidRentalDetailsError as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/{rental_id}", response_model=Rental, responses={
    404: {"description": "Rental not found"},
})
@inject
async def get_rental_route(
        rental_id: UUID4,
        rental_use_cases: RentalUseCases = Depends(Provide[AppContainer.rental_use_cases]),
):
    try:
        return await rental_use_cases.get_rental(rental_id)
    except EntityNotFoundError:
        raise HTTPException(status_code=404, detail="Rental not found")


@router.delete("/{rental_id}", status_code=204, responses={
    404: {"description": "Rental not found"},
    500: {"description": "Data integrity error: car linked to rental no longer exists"},
})
@inject
async def end_rental_route(
        rental_id: UUID4,
        rental_use_cases: RentalUseCases = Depends(Provide[AppContainer.rental_use_cases]),
):
    try:
        await rental_use_cases.end_rental(rental_id)
    except EntityNotFoundError as e:
        if e.entity_id == rental_id:
            raise HTTPException(status_code=404, detail="Rental not found")
        raise HTTPException(status_code=500, detail="Data integrity error: car linked to rental no longer exists")
