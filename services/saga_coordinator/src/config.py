from pathlib import Path
from typing import List, Dict
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE_PATH = BASE_DIR / ".env"


class Settings(BaseSettings):
    # --- Service Configuration ---
    SERVICE_NAME: str = "saga_coordinator"
    ENVIRONMENT: str = Field(default="development")
    LOG_LEVEL: str = "INFO"

    # --- Database (PostgreSQL) ---
    DATABASE_URL: str = Field(..., description="PostgreSQL connection string")
    DB_POOL_MIN_SIZE: int = 5
    DB_POOL_MAX_SIZE: int = 20

    # --- Kafka (Messaging) ---
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_GROUP_ID: str = "saga_coordinator_group_v1"

    LISTEN_TOPICS: List[str] = [
        "shipment.events",
        "warehouse.events",
        "delivery.events",
        "blockchain.events"
    ]

    COMMAND_TOPICS: Dict[str, str] = {
        "shipment": "shipment.commands",
        "warehouse": "inventory.commands",
        "delivery": "delivery.commands",
        "blockchain": "blockchain.commands"
    }

    # --- Business Logic ---
    SAGA_START_EVENTS: List[str] = ["shipment.created"]
    COMPENSATION_TRIGGER_EVENTS: List[str] = [
        "inventory.insufficient",
        "delivery.failed",
        "courier.unassigned",
        "blockchain.verification_failed"
    ]
    SAGA_STEP_TIMEOUT_SECONDS: int = 3600

    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATH,
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )


settings = Settings()
