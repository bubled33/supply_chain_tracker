from typing import List, AsyncIterator, Dict, Any
import asyncio
from collections import defaultdict
from datetime import datetime

from .base import Event, Command
from .ports import EventQueuePort


class InMemoryEventQueueAdapter(EventQueuePort):

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
        if not self._producer_started:
            print(f"[MOCK] Producer started for {self._bootstrap_servers}")
            self._producer_started = True
        return self

    async def publish_event(self, event: Event, *topics: str) -> None:
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
        topics_str = ", ".join(topics)
        print(f"[MOCK] Consumer started for events topics: [{topics_str}]")

        consumer_key = f"event_consumer_{hash(topics)}"
        InMemoryEventQueueAdapter._consumers_running[consumer_key] = True

        offsets = {topic: 0 for topic in topics}

        try:
            while InMemoryEventQueueAdapter._consumers_running.get(consumer_key, False):
                received_anything = False

                for topic in topics:
                    messages = InMemoryEventQueueAdapter._events_storage.get(topic, [])
                    current_offset = offsets[topic]

                    if current_offset < len(messages):
                        for i in range(current_offset, len(messages)):
                            message = messages[i]
                            event = Event.from_dict(message['value'])
                            offsets[topic] += 1
                            print(f"[MOCK] Consumed event from '{topic}': {event.event_type}")
                            yield event
                            received_anything = True

                if not received_anything:
                    await asyncio.sleep(0.1)

        finally:
            InMemoryEventQueueAdapter._consumers_running[consumer_key] = False
            print(f"[MOCK] Consumer stopped for events topics: [{topics_str}]")

    async def consume_command(self, *topics: str) -> AsyncIterator[Command]:
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
        if self._producer_started:
            print(f"[MOCK] Producer closed for {self._bootstrap_servers}")
            self._producer_started = False

    async def __aenter__(self):
        await self._get_producer()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    @classmethod
    def clear_all_topics(cls):
        cls._events_storage.clear()
        cls._commands_storage.clear()
        cls._consumers_running.clear()
        print("[MOCK] All topics cleared")

    @classmethod
    def get_published_events(cls, topic: str) -> List[Dict[str, Any]]:
        return cls._events_storage.get(topic, [])

    @classmethod
    def get_published_commands(cls, topic: str) -> List[Dict[str, Any]]:
        return cls._commands_storage.get(topic, [])
