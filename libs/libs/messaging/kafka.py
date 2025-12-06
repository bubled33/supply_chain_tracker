from typing import List, AsyncIterator
import json
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer, ConsumerRecord

from .base import Event, Command
from .ports import EventQueuePort


class KafkaEventQueueAdapter(EventQueuePort):
    """Адаптер для работы с Kafka через aiokafka"""

    def __init__(
            self,
            bootstrap_servers: str,
            group_id: str = "default-group",
    ):
        self._bootstrap_servers = bootstrap_servers
        self._group_id = group_id
        self._producer: AIOKafkaProducer | None = None

    async def _get_producer(self) -> AIOKafkaProducer:
        """Ленивая инициализация producer"""
        if self._producer is None:
            self._producer = AIOKafkaProducer(
                bootstrap_servers=self._bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
            )
            await self._producer.start()
        return self._producer

    async def publish_event(self, event: Event, topic: str) -> None:
        """Публикация события в Kafka"""
        producer = await self._get_producer()

        # Используем aggregate_id как ключ для партиционирования
        key = str(event.aggregate_id)
        value = event.to_dict()

        await producer.send_and_wait(topic, value=value, key=key)

    async def publish_command(self, command: Command, topic: str) -> None:
        """Публикация команды в Kafka"""
        producer = await self._get_producer()

        key = str(command.aggregate_id)
        value = {
            'command_id': str(command.command_id),
            'command_type': command.command_type,
            'aggregate_id': str(command.aggregate_id),
            'payload': command.payload,
            'correlation_id': str(command.correlation_id) if command.correlation_id else None
        }

        await producer.send_and_wait(topic, value=value, key=key)

    async def consume_event(self, topic: str) -> AsyncIterator[Event]:
        """Чтение событий из Kafka"""
        consumer = AIOKafkaConsumer(
            topic,
            bootstrap_servers=self._bootstrap_servers,
            group_id=self._group_id,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            key_deserializer=lambda k: k.decode('utf-8') if k else None,
            auto_offset_reset='earliest',  # Читать с начала при первом подключении
            enable_auto_commit=True,  # Автокоммит offset
        )

        await consumer.start()
        try:
            async for message in consumer:
                yield Event.from_dict(message.value)
        finally:
            await consumer.stop()

    async def consume_command(self, topic: str) -> AsyncIterator[Command]:
        """Чтение команд из Kafka"""
        consumer = AIOKafkaConsumer(
            topic,
            bootstrap_servers=self._bootstrap_servers,
            group_id=self._group_id,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            key_deserializer=lambda k: k.decode('utf-8') if k else None,
            auto_offset_reset='earliest',
            enable_auto_commit=True,
        )

        await consumer.start()
        try:
            async for message in consumer:
                yield Command.from_dict(message.value)
        finally:
            await consumer.stop()

    async def close(self) -> None:
        """Закрыть producer при завершении"""
        if self._producer is not None:
            await self._producer.stop()
            self._producer = None
