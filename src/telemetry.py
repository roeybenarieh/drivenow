import logging
import logging.config

from fastapi import FastAPI
from opentelemetry import metrics
from opentelemetry.exporter.prometheus import PrometheusMetricReader
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.metrics import Counter
from opentelemetry.sdk.metrics import MeterProvider, Meter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME
from prometheus_client import start_http_server
from sqlalchemy import Engine

from src.config import LoggingSettings, MetricsSettings


def setup_meter(settings: MetricsSettings) -> Meter:
    resource = Resource({SERVICE_NAME: settings.service_name})
    provider = MeterProvider(resource=resource, metric_readers=[PrometheusMetricReader()])
    metrics.set_meter_provider(provider)
    start_http_server(port=settings.port, addr=settings.address)
    return metrics.get_meter(settings.meter_name)


def setup_logger(settings: LoggingSettings) -> logging.Logger:
    if settings.config:
        logging.config.dictConfig(settings.config)
    return logging.getLogger(settings.logger_name)


def create_rabbitmq_car_errors_counter(meter: Meter) -> Counter:
    return meter.create_counter(
        "drivenow.rabbitmq.car.errors",
        description="RabbitMQ car handler errors",
    )


def create_rabbitmq_rental_errors_counter(meter: Meter) -> Counter:
    return meter.create_counter(
        "drivenow.rabbitmq.rental.errors",
        description="RabbitMQ rental handler errors",
    )


def instrument_fastapi(app: FastAPI) -> None:
    FastAPIInstrumentor.instrument_app(app)


def instrument_sqlalchemy(engine: Engine) -> None:
    SQLAlchemyInstrumentor().instrument(engine=engine)
