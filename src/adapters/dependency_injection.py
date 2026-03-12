from dependency_injector import containers, providers
from sqlalchemy.ext.asyncio import async_sessionmaker

from src.adapters.postgres.uow import PgUnitOfWork
from src.adapters.postgres.utils import get_engine
from src.application.use_cases import CarUseCases, RentalUseCases
from src.config import read_app_config, AppSettings
from src.domain.service import RentalService
from src.telemetry import (
    setup_logger,
    setup_meter,
    create_rabbitmq_car_errors_counter,
    create_rabbitmq_rental_errors_counter,
)


class AppContainer(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(
        packages=["src.adapters.fastapi", "src.adapters.rabbitmq"],
    )

    config: providers.Singleton[AppSettings] = providers.Singleton(read_app_config)

    # database
    engine = providers.Resource(
        get_engine,
        config().postgres.dsn.unicode_string(),
    )
    session_factory = providers.ContextLocalSingleton(
        async_sessionmaker, engine, expire_on_commit=False, autocommit=False
    )
    uow = providers.Factory(PgUnitOfWork, session_factory=session_factory)

    # observability
    logger = providers.Singleton(setup_logger, config().observability.logging)
    meter = providers.Singleton(setup_meter, config().observability.metrics)
    rabbitmq_car_errors = providers.Singleton(create_rabbitmq_car_errors_counter, meter=meter)
    rabbitmq_rental_errors = providers.Singleton(create_rabbitmq_rental_errors_counter, meter=meter)

    # application layer
    car_use_cases = providers.Factory(CarUseCases, uow=uow, logger=logger, meter=meter)
    rental_service = providers.Singleton(RentalService)
    rental_use_cases = providers.Factory(RentalUseCases, uow=uow, logger=logger, meter=meter, service=rental_service)
