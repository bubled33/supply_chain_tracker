from typing import List
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- Service Configuration ---
    SERVICE_NAME: str = "blockchain_worker"
    ENVIRONMENT: str = Field(default="development")
    LOG_LEVEL: str = "INFO"

    # --- Kafka (Messaging) ---
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_GROUP_ID: str = "blockchain_recorder_group_v1"
    LISTEN_TOPICS: List[str] = [
        "shipment_service",
        "delivery_service",
        "warehouse_service"
    ]

    # --- Redis (Infrastructure) ---
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_NONCE_KEY_PREFIX: str = "blockchain:nonce:"

    # --- Blockchain (Web3) ---
    BLOCKCHAIN_RPC_URL: str = Field(...)
    BLOCKCHAIN_PRIVATE_KEY: SecretStr = Field(...)
    BLOCKCHAIN_CHAIN_ID: int = Field(default=11155111)
    BLOCKCHAIN_GAS_LIMIT: int = 100_000

    # --- Business Logic Filters ---
    TARGET_EVENTS: List[str] = [
        "shipment.created",
        "shipment.updated",
        "delivery.completed",
        "inventory.released"
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
