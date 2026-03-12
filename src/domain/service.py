from datetime import datetime

from src.domain.models import Car, CarStatus, Rental


class RentalService:
    @staticmethod
    def create_rental(
            car: Car,
            customer_name: str,
            start_date: datetime,
            end_date: datetime,
    ) -> Rental:
        """
        Validates car is AVAILABLE, transitions it to IN_USE, and returns a new Rental.

        Raises:
            InvalidCarDetailsError: If the car state cannot change to "in-use".
            InvalidRentalDetailsError: If customer_name is empty or end_date <= start_date.
        """
        # creating the rental object first in case of an invalid rental details error
        rental = Rental(car_id=car.id, customer_name=customer_name, start_date=start_date, end_date=end_date)
        car.status = CarStatus.IN_USE
        return rental
