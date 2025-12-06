from typing import List, AsyncIterator, Dict, Any
import json
import asyncio
from collections import defaultdict
from datetime import datetime

from .base import Event, Command
from .ports import EventQueuePort


class InMemoryEventQueueAdapter(EventQueuePort):
    """
    In-memory mock адаптер для тестирования без Kafka.
    Хранит события и команды в памяти.
    """

    # Shared storage между экземплярами (имитация Kafka topics)
    _events_storage: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    _commands_storage: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    _consumers_running: Dict[str, bool] = defaultdict(bool)

    def __init__(
            self,
            bootstrap_servers: str = "mock",
            group_id: str = "default-group",
    ):
        self._bootstrap_servers = bootstrap_servers
        self._group_id = group_id
        self._producer_started = False

    async def _get_producer(self):
        """Mock producer initialization"""
        if not self._producer_started:
            print(f"[MOCK] Producer started for {self._bootstrap_servers}")
            self._producer_started = True
        return self

    async def publish_event(self, event: Event, topic: str) -> None:
        """Публикация события в память"""
        value = event.to_dict()
        key = str(event.aggregate_id)

        message = {
            'key': key,
            'value': value,
            'topic': topic,
            'timestamp': datetime.utcnow().isoformat(),
        }

        InMemoryEventQueueAdapter._events_storage[topic].append(message)
        print(f"[MOCK] Published event to '{topic}': {event.event_type} (id={event.event_id})")

    async def publish_command(self, command: Command, topic: str) -> None:
        """Публикация команды в память"""
        key = str(command.aggregate_id)
        value = {
            'command_id': str(command.command_id),
            'command_type': command.command_type,
            'aggregate_id': str(command.aggregate_id),
            'payload': command.payload,
            'correlation_id': str(command.correlation_id) if command.correlation_id else None
        }

        message = {
            'key': key,
            'value': value,
            'topic': topic,
            'timestamp': datetime.utcnow().isoformat(),
        }

        InMemoryEventQueueAdapter._commands_storage[topic].append(message)
        print(f"[MOCK] Published command to '{topic}': {command.command_type} (id={command.command_id})")

    async def consume_event(self, topic: str) -> AsyncIterator[Event]:
        """Чтение событий из памяти (polling)"""
        print(f"[MOCK] Consumer started for events topic '{topic}'")
        InMemoryEventQueueAdapter._consumers_running[f"event_{topic}"] = True

        consumed_count = 0

        try:
            while InMemoryEventQueueAdapter._consumers_running.get(f"event_{topic}", False):
                messages = InMemoryEventQueueAdapter._events_storage.get(topic, [])

                # Читаем новые сообщения начиная с consumed_count
                for i in range(consumed_count, len(messages)):
                    message = messages[i]
                    event = Event.from_dict(message['value'])
                    consumed_count += 1
                    print(f"[MOCK] Consumed event from '{topic}': {event.event_type}")
                    yield event

                # Polling интервал
                await asyncio.sleep(0.1)
        finally:
            InMemoryEventQueueAdapter._consumers_running[f"event_{topic}"] = False
            print(f"[MOCK] Consumer stopped for events topic '{topic}'")

    async def consume_command(self, topic: str) -> AsyncIterator[Command]:
        """Чтение команд из памяти (polling)"""
        print(f"[MOCK] Consumer started for commands topic '{topic}'")
        InMemoryEventQueueAdapter._consumers_running[f"command_{topic}"] = True

        consumed_count = 0

        try:
            while InMemoryEventQueueAdapter._consumers_running.get(f"command_{topic}", False):
                messages = InMemoryEventQueueAdapter._commands_storage.get(topic, [])

                # Читаем новые сообщения начиная с consumed_count
                for i in range(consumed_count, len(messages)):
                    message = messages[i]
                    command = Command.from_dict(message['value'])
                    consumed_count += 1
                    print(f"[MOCK] Consumed command from '{topic}': {command.command_type}")
                    yield command

                # Polling интервал
                await asyncio.sleep(0.1)
        finally:
            InMemoryEventQueueAdapter._consumers_running[f"command_{topic}"] = False
            print(f"[MOCK] Consumer stopped for commands topic '{topic}'")

    async def close(self) -> None:
        """Закрыть mock producer"""
        if self._producer_started:
            print(f"[MOCK] Producer closed for {self._bootstrap_servers}")
            self._producer_started = False

    async def __aenter__(self):
        """Async context manager entry"""
        await self._get_producer()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()

    @classmethod
    def clear_all_topics(cls):
        """Очистить все топики (для тестов)"""
        cls._events_storage.clear()
        cls._commands_storage.clear()
        cls._consumers_running.clear()
        print("[MOCK] All topics cleared")

    @classmethod
    def get_published_events(cls, topic: str) -> List[Dict[str, Any]]:
        """Получить все опубликованные события в топик (для тестов)"""
        return cls._events_storage.get(topic, [])

    @classmethod
    def get_published_commands(cls, topic: str) -> List[Dict[str, Any]]:
        """Получить все опубликованные команды в топик (для тестов)"""
        return cls._commands_storage.get(topic, [])
