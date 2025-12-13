from typing import List, AsyncIterator, Dict, Any
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

    async def publish_event(self, event: Event, *topics: str) -> None:
        """Публикация события в один или несколько топиков в памяти"""
        value = event.to_dict()
        key = str(event.aggregate_id)

        for topic in topics:
            message = {
                'key': key,
                'value': value,
                'topic': topic,
                'timestamp': datetime.utcnow().isoformat(),
            }

            InMemoryEventQueueAdapter._events_storage[topic].append(message)
            print(f"[MOCK] Published event to '{topic}': {event.event_type} (id={event.event_id})")

    async def publish_command(self, command: Command, *topics: str) -> None:
        """Публикация команды в один или несколько топиков в памяти"""
        key = str(command.aggregate_id)
        value = {
            'command_id': str(command.command_id),
            'command_type': command.command_type,
            'aggregate_id': str(command.aggregate_id),
            'payload': command.payload,
            'correlation_id': str(command.correlation_id) if command.correlation_id else None
        }

        for topic in topics:
            message = {
                'key': key,
                'value': value,
                'topic': topic,
                'timestamp': datetime.utcnow().isoformat(),
            }

            InMemoryEventQueueAdapter._commands_storage[topic].append(message)
            print(f"[MOCK] Published command to '{topic}': {command.command_type} (id={command.command_id})")

    async def consume_event(self, *topics: str) -> AsyncIterator[Event]:
        """Чтение событий из одного или нескольких топиков (polling)"""
        topics_str = ", ".join(topics)
        print(f"[MOCK] Consumer started for events topics: [{topics_str}]")

        # Ключ для остановки консьюмера — уникальный для набора топиков или одного вызова
        # Для упрощения используем составной ключ
        consumer_key = f"event_consumer_{hash(topics)}"
        InMemoryEventQueueAdapter._consumers_running[consumer_key] = True

        # Отслеживаем offset для каждого топика отдельно
        offsets = {topic: 0 for topic in topics}

        try:
            while InMemoryEventQueueAdapter._consumers_running.get(consumer_key, False):
                received_anything = False

                for topic in topics:
                    messages = InMemoryEventQueueAdapter._events_storage.get(topic, [])
                    current_offset = offsets[topic]

                    # Читаем новые сообщения начиная с current_offset для данного топика
                    if current_offset < len(messages):
                        # Читаем все доступные новые сообщения пачкой
                        for i in range(current_offset, len(messages)):
                            message = messages[i]
                            event = Event.from_dict(message['value'])
                            offsets[topic] += 1
                            print(f"[MOCK] Consumed event from '{topic}': {event.event_type}")
                            yield event
                            received_anything = True

                # Если ничего не прочитали ни из одного топика, спим
                if not received_anything:
                    await asyncio.sleep(0.1)

        finally:
            InMemoryEventQueueAdapter._consumers_running[consumer_key] = False
            print(f"[MOCK] Consumer stopped for events topics: [{topics_str}]")

    async def consume_command(self, *topics: str) -> AsyncIterator[Command]:
        """Чтение команд из одного или нескольких топиков (polling)"""
        topics_str = ", ".join(topics)
        print(f"[MOCK] Consumer started for commands topics: [{topics_str}]")

        consumer_key = f"command_consumer_{hash(topics)}"
        InMemoryEventQueueAdapter._consumers_running[consumer_key] = True

        offsets = {topic: 0 for topic in topics}

        try:
            while InMemoryEventQueueAdapter._consumers_running.get(consumer_key, False):
                received_anything = False

                for topic in topics:
                    messages = InMemoryEventQueueAdapter._commands_storage.get(topic, [])
                    current_offset = offsets[topic]

                    if current_offset < len(messages):
                        for i in range(current_offset, len(messages)):
                            message = messages[i]
                            command = Command.from_dict(message['value'])
                            offsets[topic] += 1
                            print(f"[MOCK] Consumed command from '{topic}': {command.command_type}")
                            yield command
                            received_anything = True

                if not received_anything:
                    await asyncio.sleep(0.1)
        finally:
            InMemoryEventQueueAdapter._consumers_running[consumer_key] = False
            print(f"[MOCK] Consumer stopped for commands topics: [{topics_str}]")

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
