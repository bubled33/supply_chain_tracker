import json
import asyncio
from typing import AsyncIterator, Optional

from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from aiokafka.errors import KafkaError

from libs.observability.logger import get_json_logger
from .base import Event, Command
from .ports import EventQueuePort

logger = get_json_logger(__name__)


class KafkaEventQueueAdapter(EventQueuePort):
    """
    Адаптер для работы с Kafka через aiokafka.
    Включает:
    - Идемпотентность продюсера (Exactly-once delivery semantics на уровне партиции)
    - Политику ретраев (Exponential Backoff) при отправке
    - Read Committed уровень изоляции для консьюмера
    """

    def __init__(
            self,
            bootstrap_servers: str,
            group_id: str = "default-group",
            max_retries: int = 5,
            initial_backoff: float = 0.5
    ):
        self._bootstrap_servers = bootstrap_servers
        self._group_id = group_id
        self._producer: Optional[AIOKafkaProducer] = None

        # Настройки ретраев (App-level retries)
        self._max_retries = max_retries
        self._initial_backoff = initial_backoff

    async def _get_producer(self) -> AIOKafkaProducer:
        """Ленивая инициализация producer с настройками надежности"""
        if self._producer is None:
            self._producer = AIOKafkaProducer(
                bootstrap_servers=self._bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,

                enable_idempotence=True,
                acks='all',

                retry_backoff_ms=100,
                request_timeout_ms=5000,
            )
            await self._producer.start()
            logger.info(
                "Kafka Producer started with idempotence enabled",
                extra={"bootstrap_servers": self._bootstrap_servers}
            )
        return self._producer

    async def _send_with_retry(self, topic: str, value: dict, key: str) -> None:
        """
        Обертка для отправки с экспоненциальным backoff.
        Защищает от временных падений брокера.
        """
        producer = await self._get_producer()

        for attempt in range(1, self._max_retries + 1):
            try:
                await producer.send_and_wait(topic, value=value, key=key)
                return  # Успех
            except KafkaError as e:
                if attempt == self._max_retries:
                    logger.error(
                        f"Failed to send to Kafka after {attempt} attempts",
                        extra={
                            "topic": topic,
                            "error": str(e),
                            "key": key
                        },
                        exc_info=True
                    )
                    raise e

                sleep_time = self._initial_backoff * (2 ** (attempt - 1))
                logger.warning(
                    f"Kafka send failed. Retrying in {sleep_time}s...",
                    extra={
                        "attempt": attempt,
                        "max_retries": self._max_retries,
                        "error": str(e),
                        "topic": topic
                    }
                )
                await asyncio.sleep(sleep_time)

    async def publish_event(self, event: Event, *topics: str) -> None:
        """Публикация события в несколько топиков Kafka с ретраями"""
        key = str(event.aggregate_id)
        value = event.to_dict()

        for topic in topics:
            await self._send_with_retry(topic, value=value, key=key)
            logger.debug(
                f"Event published: {event.event_type}",
                extra={"topic": topic, "event_id": str(event.event_id)}
            )

    async def publish_command(self, command: Command, *topics: str) -> None:
        """Публикация команды в несколько топиков Kafka с ретраями"""
        key = str(command.aggregate_id)
        value = {
            'command_id': str(command.command_id),
            'command_type': command.command_type,
            'aggregate_id': str(command.aggregate_id),
            'payload': command.payload,
            'correlation_id': str(command.correlation_id) if command.correlation_id else None
        }

        for topic in topics:
            await self._send_with_retry(topic, value=value, key=key)
            logger.debug(
                f"Command published: {command.command_type}",
                extra={"topic": topic, "command_id": str(command.command_id)}
            )

    async def consume_event(self, *topics: str) -> AsyncIterator[Event]:
        """Чтение событий из нескольких топиков Kafka"""
        consumer = AIOKafkaConsumer(
            *topics,
            bootstrap_servers=self._bootstrap_servers,
            group_id=self._group_id,

            key_deserializer=lambda k: k.decode('utf-8') if k else None,
            # Десериализатор выносим в логику цикла

            auto_offset_reset='earliest',
            enable_auto_commit=True,
            isolation_level="read_committed",
            session_timeout_ms=10000,
            heartbeat_interval_ms=3000,
        )

        await consumer.start()
        logger.info("Kafka Event Consumer started", extra={"topics": list(topics)})

        try:
            async for message in consumer:
                try:
                    val = json.loads(message.value.decode('utf-8'))
                    event = Event.from_dict(val)
                    yield event
                except json.JSONDecodeError:
                    logger.error(
                        "Failed to deserialize JSON event",
                        extra={
                            "topic": message.topic,
                            "offset": message.offset,
                            "partition": message.partition
                        }
                    )
                    continue
                except Exception as e:
                    logger.error(
                        f"Error processing message: {e}",
                        extra={
                            "topic": message.topic,
                            "offset": message.offset
                        },
                        exc_info=True
                    )
                    continue
        finally:
            await consumer.stop()

    async def consume_command(self, *topics: str) -> AsyncIterator[Command]:
        """Чтение команд из нескольких топиков Kafka"""
        consumer = AIOKafkaConsumer(
            *topics,
            bootstrap_servers=self._bootstrap_servers,
            group_id=self._group_id,
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            isolation_level="read_committed",
        )

        await consumer.start()
        logger.info("Kafka Command Consumer started", extra={"topics": list(topics)})

        try:
            async for message in consumer:
                try:
                    val = json.loads(message.value.decode('utf-8'))
                    command = Command.from_dict(val)
                    yield command
                except (json.JSONDecodeError, KeyError, ValueError) as e:
                    logger.error(
                        "Invalid command format",
                        extra={
                            "topic": message.topic,
                            "offset": message.offset,
                            "error": str(e)
                        }
                    )
                    continue
        finally:
            await consumer.stop()

    async def close(self) -> None:
        """Закрыть producer при завершении"""
        if self._producer is not None:
            await self._producer.stop()
            self._producer = None
            logger.info("Kafka Producer closed")

    async def __aenter__(self) -> 'KafkaEventQueueAdapter':
        await self._get_producer()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()
