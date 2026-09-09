"""Configuration management for NexAlert backend

Environment-based configuration using Pydantic Settings.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Backend configuration"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://nexalert:nexalert@localhost:5432/nexalert_dev",
        description="PostgreSQL connection URL (async)"
    )

    # MQTT Broker
    mqtt_broker_host: str = Field(
        default="localhost",
        description="MQTT broker hostname/IP"
    )
    mqtt_broker_port: int = Field(
        default=1883,
        description="MQTT broker port"
    )
    mqtt_topic: str = Field(
        default="Nexalert/telemetry/node1",
        description="MQTT telemetry topic (locked development format)"
    )
    mqtt_client_id: str = Field(
        default="nexalert-backend",
        description="MQTT client ID"
    )
    mqtt_username: str | None = Field(
        default=None,
        description="MQTT username (None = no auth)"
    )
    mqtt_password: str | None = Field(
        default=None,
        description="MQTT password (None = no auth)"
    )
    mqtt_reconnect_delay_s: int = Field(
        default=5,
        description="MQTT reconnect delay in seconds"
    )

    # API
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, description="API port")
    api_reload: bool = Field(default=False, description="Enable hot reload")

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")

    # Telemetry validation
    telemetry_schema_path: str = Field(
        default="../../schemas/telemetry-envelope.schema.json",
        description="Path to canonical telemetry schema"
    )


# Global settings instance
settings = Settings()
