from datetime import datetime
from uuid import UUID

import pytest

from src.domain.models import Car, CarStatus, InvalidCarDetailsError, InvalidRentalDetailsError, Rental


def make_car(status: CarStatus = CarStatus.AVAILABLE) -> Car:
    car = Car(model="BMW", year=2020, status=CarStatus.AVAILABLE)
    if status != CarStatus.AVAILABLE:
        car.status = status
    return car


class TestCarConstruction:
    def test_valid_car_fields(self):
        car = Car(model="BMW", year=2020, status=CarStatus.AVAILABLE)
        assert car.model == "BMW"
        assert car.year == 2020
        assert car.status == CarStatus.AVAILABLE
        assert isinstance(car.id, UUID)

    def test_empty_model_raises(self):
        with pytest.raises(InvalidCarDetailsError):
            Car(model="", year=2020, status=CarStatus.AVAILABLE)

    def test_year_before_1885_raises(self):
        with pytest.raises(InvalidCarDetailsError):
            Car(model="BMW", year=1884, status=CarStatus.AVAILABLE)

    def test_year_1885_is_valid(self):
        car = Car(model="BMW", year=1885, status=CarStatus.AVAILABLE)
        assert car.year == 1885

    @pytest.mark.parametrize("status", [CarStatus.IN_USE, CarStatus.UNDER_MAINTENANCE])
    def test_initial_status_must_be_available(self, status: CarStatus):
        with pytest.raises(InvalidCarDetailsError):
            Car(model="BMW", year=2020, status=status)

    def test_each_car_gets_unique_id(self):
        car_a = Car(model="BMW", year=2020, status=CarStatus.AVAILABLE)
        car_b = Car(model="BMW", year=2020, status=CarStatus.AVAILABLE)
        assert car_a.id != car_b.id


class TestCarStatusTransitions:
    @pytest.mark.parametrize("status", [CarStatus.IN_USE, CarStatus.UNDER_MAINTENANCE])
    def test_available_to(self, status: CarStatus):
        car = make_car()
        car.status = status
        assert car.status == status

    @pytest.mark.parametrize("initial", [CarStatus.IN_USE, CarStatus.UNDER_MAINTENANCE])
    def test_to_available(self, initial: CarStatus):
        car = make_car(initial)
        car.status = CarStatus.AVAILABLE
        assert car.status == CarStatus.AVAILABLE

    @pytest.mark.parametrize("status", list(CarStatus))
    def test_cannot_transition_to_same_status(self, status: CarStatus):
        car = make_car(status)
        with pytest.raises(InvalidCarDetailsError):
            car.status = status

    @pytest.mark.parametrize("initial,target", [
        (CarStatus.IN_USE, CarStatus.UNDER_MAINTENANCE),
        (CarStatus.UNDER_MAINTENANCE, CarStatus.IN_USE),
    ])
    def test_cannot_transition_between_non_available(self, initial: CarStatus, target: CarStatus):
        car = make_car(initial)
        with pytest.raises(InvalidCarDetailsError):
            car.status = target

    @pytest.mark.parametrize("intermediate", [CarStatus.IN_USE, CarStatus.UNDER_MAINTENANCE])
    def test_full_cycle_back_to_available(self, intermediate: CarStatus):
        car = make_car()
        car.status = intermediate
        car.status = CarStatus.AVAILABLE
        assert car.status == CarStatus.AVAILABLE


class TestRentalConstruction:
    START = datetime(2024, 6, 1, 10, 0)
    END = datetime(2024, 6, 8, 10, 0)

    def test_valid_rental(self):
        car = make_car()
        rental = Rental(car_id=car.id, customer_name="Alice", start_date=self.START, end_date=self.END)
        assert rental.car_id == car.id
        assert rental.customer_name == "Alice"
        assert rental.start_date == self.START
        assert rental.end_date == self.END
        assert isinstance(rental.id, UUID)

    def test_empty_customer_name_raises(self):
        car = make_car()
        with pytest.raises(InvalidRentalDetailsError):
            Rental(car_id=car.id, customer_name="", start_date=self.START, end_date=self.END)

    @pytest.mark.parametrize("start,end", [
        (START, START),  # equal
        (END, START),    # reversed
    ])
    def test_invalid_date_range_raises(self, start: datetime, end: datetime):
        car = make_car()
        with pytest.raises(InvalidRentalDetailsError):
            Rental(car_id=car.id, customer_name="Alice", start_date=start, end_date=end)

    def test_each_rental_gets_unique_id(self):
        car = make_car()
        r1 = Rental(car_id=car.id, customer_name="Alice", start_date=self.START, end_date=self.END)
        r2 = Rental(car_id=car.id, customer_name="Alice", start_date=self.START, end_date=self.END)
        assert r1.id != r2.id
