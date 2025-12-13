from typing import Protocol, AsyncIterator

from libs.messaging.base import Event, Command


class EventQueuePort(Protocol):
    """Порт для работы с очередью событий и команд (Kafka, RabbitMQ, etc.)"""

    async def publish_event(self, event: Event, *topics: str) -> None:
        """Опубликовать событие в один или несколько топиков"""
        ...

    async def publish_command(self, command: Command, *topics: str) -> None:
        """Опубликовать команду в один или несколько топиков"""
        ...

    def consume_event(self, *topics: str) -> AsyncIterator[Event]:
        """Читать события из одного или нескольких топиков"""
        ...

    def consume_command(self, *topics: str) -> AsyncIterator[Command]:
        """Читать команды из одного или нескольких топиков"""
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
