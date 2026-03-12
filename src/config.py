from typing import Self, Any

import yaml
from pydantic import FilePath, BaseModel, PostgresDsn, AmqpDsn, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvironmentSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra='ignore', case_sensitive=False)

    configuration_file_path: FilePath


class FastAPISettings(BaseModel):
    address: str
    port: int


class RabbitMQSettings(BaseModel):
    dsn: AmqpDsn
    queue_name: str


class PostgresSettings(BaseModel):
    dsn: PostgresDsn


class LoggingSettings(BaseModel):
    logger_name: str
    config: dict[str, Any] | None


class MetricsSettings(BaseModel):
    service_name: str
    meter_name: str
    address: str
    port: int


class ObservabilitySettings(BaseModel):
    logging: LoggingSettings
    metrics: MetricsSettings


class AppSettings(BaseModel):
    fastAPI: FastAPISettings | None = None
    rabbitmq: RabbitMQSettings | None = None
    postgres: PostgresSettings
    observability: ObservabilitySettings

    @model_validator(mode="after")
    def require_at_least_one_inbound_adapter(self) -> Self:
        if (self.fastAPI, self.rabbitmq) == (None, None):
            raise ValueError("at least one inbound adapter (fastAPI or rabbitmq) must be configured")
        return self


def read_app_config() -> AppSettings:
    """Read and parse the application configuration file into an AppSettings instance.

    Loads the config file path from environment variables, reads the YAML file,
    and validates its contents against the AppSettings model.

    Returns:
        AppSettings: The validated application configuration.

    Raises:
        pydantic.ValidationError: If environment variables are invalid or missing,
            or if the YAML content does not match the expected AppSettings schema.
        yaml.YAMLError: If the configuration file contains invalid YAML.
    """
    settings = EnvironmentSettings()  # type: ignore[call-arg]
    with open(settings.configuration_file_path) as config_file:
        data = yaml.safe_load(config_file)

    if data is None:
        raise ValueError("application configuration file is empty")
    return AppSettings(**data)
