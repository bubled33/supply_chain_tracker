import asyncio
import uuid
import uvicorn
import asyncpg
import redis.asyncio as redis
from fastapi import FastAPI
from eth_account import Account
from web3 import AsyncWeb3, AsyncHTTPProvider

from libs.messaging.kafka import KafkaEventQueueAdapter
from libs.observability.logger import set_environment, set_correlation_id, set_service_name, get_json_logger
from libs.observability.metrics import metrics_endpoint

from src.app.services.blockhain import BlockchainService
from src.app.workers.confirmation_monitor import ConfirmationMonitor
from src.config import settings
from src.app.workers.worker import BlockchainWorker
from src.infra.db.blockhain_repository import AsyncPostgresBlockchainRepository
from src.infra.redis_nonse_manager import RedisNonceManager
from src.infra.web3_blockhain_gateway import Web3BlockchainGateway

logger = get_json_logger("main", level=settings.LOG_LEVEL)


def create_metrics_app() -> FastAPI:
    app = FastAPI()
    app.add_api_route("/metrics", metrics_endpoint, methods=["GET"])
    return app


async def main():
    set_service_name(settings.SERVICE_NAME)
    set_environment(settings.ENVIRONMENT)
    set_correlation_id(str(uuid.uuid4()))

    logger.info("Starting Blockchain Service...")

    redis_client = redis.from_url(settings.REDIS_URL)
    pg_pool = await asyncpg.create_pool(dsn=settings.DATABASE_URL)
    w3_provider = AsyncWeb3(AsyncHTTPProvider(settings.BLOCKCHAIN_RPC_URL))

    metrics_app = create_metrics_app()
    # Запускаем метрики на отдельном порту или на 8000, если в поде один сервис
    metrics_config = uvicorn.Config(metrics_app, host="0.0.0.0", port=8000, log_config=None)
    metrics_server = uvicorn.Server(metrics_config)

    try:
        # Infrastructure
        nonce_manager = RedisNonceManager(
            redis=redis_client,
            w3=w3_provider,
            key_prefix=settings.REDIS_NONCE_KEY_PREFIX
        )

        account = Account.from_key(settings.BLOCKCHAIN_PRIVATE_KEY.get_secret_value())
        await nonce_manager.sync_from_chain(account.address)

        gateway = Web3BlockchainGateway(
            node_url=settings.BLOCKCHAIN_RPC_URL,
            private_key=settings.BLOCKCHAIN_PRIVATE_KEY.get_secret_value(),
            nonce_manager=nonce_manager,
            chain_id=settings.BLOCKCHAIN_CHAIN_ID
        )

        repository = AsyncPostgresBlockchainRepository(pg_pool)

        # Messaging
        async with KafkaEventQueueAdapter(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                group_id=settings.KAFKA_GROUP_ID
        ) as queue:

            # Application Service
            service = BlockchainService(
                repository=repository,
                gateway=gateway,
                queue=queue
            )

            # Workers
            worker = BlockchainWorker(
                queue=queue,
                service=service,
                listen_topics=settings.LISTEN_TOPICS,
                target_events=settings.TARGET_EVENTS
            )

            monitor = ConfirmationMonitor(
                service=service,
                repository=repository,
                interval_seconds=10
            )

            logger.info("Service initialized. Starting workers and metrics server...")

            await asyncio.gather(
                worker.run(),
                monitor.run(),
                metrics_server.serve()
            )

    except Exception:
        logger.critical("Critical failure in main loop", exc_info=True)
        raise
    finally:
        await redis_client.aclose()
        await pg_pool.close()


if __name__ == "__main__":
    asyncio.run(main())
