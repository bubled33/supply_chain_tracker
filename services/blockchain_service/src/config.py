from typing import List
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    SERVICE_NAME: str = "blockchain_worker"
    ENVIRONMENT: str = Field(default="development")
    LOG_LEVEL: str = "INFO"
    HOST: str = "0.0.0.0"
    PORT: int = 8004

    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_GROUP_ID: str = "blockchain_recorder_group_v1"
    LISTEN_TOPICS: List[str] = [
        "shipment_service",
        "delivery_service",
        "warehouse_service"
    ]

    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/supply_chain"

    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_NONCE_KEY_PREFIX: str = "blockchain:nonce:"

    USE_MOCK_BLOCKCHAIN: bool = False
    BLOCKCHAIN_RPC_URL: str = Field(default="https://rpc.example.com")
    BLOCKCHAIN_PRIVATE_KEY: SecretStr = Field(default="0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80")
    BLOCKCHAIN_CHAIN_ID: int = Field(default=11155111)
    BLOCKCHAIN_GAS_LIMIT: int = 100_000

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
