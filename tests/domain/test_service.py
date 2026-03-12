from datetime import datetime

import pytest

from src.domain.models import Car, CarStatus, InvalidCarDetailsError, InvalidRentalDetailsError, Rental
from src.domain.service import RentalService

START = datetime(2024, 6, 1, 10, 0)
END = datetime(2024, 6, 8, 10, 0)


def make_available_car() -> Car:
    return Car(model="Toyota Corolla", year=2021, status=CarStatus.AVAILABLE)


class TestRentalServiceCreateRental:
    def test_creates_rental_with_correct_fields(self):
        car = make_available_car()
        rental = RentalService.create_rental(car, "Bob", START, END)
        assert isinstance(rental, Rental)
        assert rental.car_id == car.id
        assert rental.customer_name == "Bob"
        assert rental.start_date == START
        assert rental.end_date == END

    def test_transitions_car_to_in_use(self):
        car = make_available_car()
        RentalService.create_rental(car, "Bob", START, END)
        assert car.status == CarStatus.IN_USE

    @pytest.mark.parametrize("status", [CarStatus.IN_USE, CarStatus.UNDER_MAINTENANCE])
    def test_unavailable_car_raises(self, status: CarStatus):
        car = make_available_car()
        car.status = status
        with pytest.raises(InvalidCarDetailsError):
            RentalService.create_rental(car, "Bob", START, END)

    def test_empty_customer_name_raises(self):
        car = make_available_car()
        with pytest.raises(InvalidRentalDetailsError):
            RentalService.create_rental(car, "", START, END)

    @pytest.mark.parametrize("start,end", [
        (END, START),  # reversed
        (START, START),  # equal
    ])
    def test_invalid_date_range_raises(self, start: datetime, end: datetime):
        car = make_available_car()
        with pytest.raises(InvalidRentalDetailsError):
            RentalService.create_rental(car, "Bob", start, end)

    def test_car_status_unchanged_when_rental_details_invalid(self):
        car = make_available_car()
        with pytest.raises(InvalidRentalDetailsError):
            RentalService.create_rental(car, "", START, END)
        assert car.status == CarStatus.AVAILABLE
