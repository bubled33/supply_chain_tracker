import asyncio
import time
from abc import ABC, abstractmethod

import asyncpg
from redis import asyncio as aioredis
from aiokafka import AIOKafkaProducer

from .dto import ComponentHealth, HealthStatus


class HealthCheck(ABC):
    """Базовый класс для health checks"""

    def __init__(self, name: str, timeout: float = 5.0):
        self.name = name
        self.timeout = timeout

    @abstractmethod
    async def check(self) -> ComponentHealth:
        """Проверка компонента"""
        pass


class PostgresHealthCheck(HealthCheck):
    """Проверка подключения к PostgreSQL"""

    def __init__(self, pool: asyncpg.Pool, timeout: float = 5.0):
        super().__init__("postgresql", timeout)
        self.pool = pool

    async def check(self) -> ComponentHealth:
        start = time.time()
        try:
            async with asyncio.timeout(self.timeout):
                async with self.pool.acquire() as conn:
                    await conn.fetchval("SELECT 1")

            latency = (time.time() - start) * 1000
            return ComponentHealth(
                status=HealthStatus.HEALTHY,
                latency_ms=round(latency, 2)
            )
        except asyncio.TimeoutError:
            return ComponentHealth(
                status=HealthStatus.UNHEALTHY,
                details={"error": "Connection timeout"}
            )
        except Exception as e:
            return ComponentHealth(
                status=HealthStatus.UNHEALTHY,
                details={"error": str(e)}
            )


class RedisHealthCheck(HealthCheck):
    """Проверка подключения к Redis"""

    def __init__(self, redis_url: str, timeout: float = 5.0):
        super().__init__("redis", timeout)
        self.redis_url = redis_url

    async def check(self) -> ComponentHealth:
        start = time.time()
        try:
            async with asyncio.timeout(self.timeout):
                redis = await aioredis.from_url(self.redis_url)
                await redis.ping()
                await redis.close()

            latency = (time.time() - start) * 1000
            return ComponentHealth(
                status=HealthStatus.HEALTHY,
                latency_ms=round(latency, 2)
            )
        except Exception as e:
            return ComponentHealth(
                status=HealthStatus.UNHEALTHY,
                details={"error": str(e)}
            )


class KafkaHealthCheck(HealthCheck):
    """Проверка подключения к Kafka"""

    def __init__(self, bootstrap_servers: str, timeout: float = 5.0):
        super().__init__("kafka", timeout)
        self.bootstrap_servers = bootstrap_servers

    async def check(self) -> ComponentHealth:
        start = time.time()
        producer = None
        try:
            async with asyncio.timeout(self.timeout):
                producer = AIOKafkaProducer(
                    bootstrap_servers=self.bootstrap_servers
                )
                await producer.start()
                # Получаем список топиков для проверки связи
                await producer.client.force_metadata_update()

            latency = (time.time() - start) * 1000
            return ComponentHealth(
                status=HealthStatus.HEALTHY,
                latency_ms=round(latency, 2)
            )
        except Exception as e:
            return ComponentHealth(
                status=HealthStatus.UNHEALTHY,
                details={"error": str(e)}
            )
        finally:
            if producer:
                await producer.stop()
