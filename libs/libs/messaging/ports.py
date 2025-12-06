from typing import Protocol, AsyncIterator

from libs.messaging.base import Event, Command


class EventQueuePort(Protocol):
    """Порт для работы с очередью событий и команд (Kafka, RabbitMQ, etc.)"""

    async def publish_event(self, event: Event, topic: str) -> None:
        """Опубликовать событие в топик"""
        ...

    async def publish_command(self, command: Command, topic: str) -> None:
        """Опубликовать команду в топик"""
        ...

    def consume_event(self, topic: str) -> AsyncIterator[Event]:
        """Читать события из топика"""
        ...

    def consume_command(self, topic: str) -> AsyncIterator[Command]:
        """Читать команды из топика"""
        ...

    async def close(self) -> None:
        """Закрыть все соединения с брокером"""
        ...

    async def __aenter__(self) -> 'EventQueuePort':
        """Async context manager entry"""
        ...

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Async context manager exit"""
        ...
