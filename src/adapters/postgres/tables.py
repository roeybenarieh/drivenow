from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Table, Uuid
from sqlalchemy.orm import registry

from src.domain.models import Car, CarStatus, Rental

registry = registry()

cars_table = Table(
    "cars",
    registry.metadata,
    Column("id", Uuid(as_uuid=True), primary_key=True),
    Column("model", String, nullable=False),
    Column("year", Integer, nullable=False),
    Column("status", Enum(CarStatus, validate_strings=True), nullable=False),
)

rentals_table = Table(
    "rentals",
    registry.metadata,
    Column("id", Uuid(as_uuid=True), primary_key=True),
    Column("car_id", Uuid(as_uuid=True), ForeignKey("cars.id"), nullable=False),
    Column("customer_name", String, nullable=False),
    Column("start_date", DateTime(timezone=True), nullable=False),
    Column("end_date", DateTime(timezone=True), nullable=False),
)

registry.map_imperatively(Car, cars_table)
registry.map_imperatively(Rental, rentals_table)
