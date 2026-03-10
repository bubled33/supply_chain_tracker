from typing import Protocol, AsyncIterator

from libs.messaging.base import Event, Command


class EventQueuePort(Protocol):

    async def publish_event(self, event: Event, *topics: str) -> None:
        ...

    async def publish_command(self, command: Command, *topics: str) -> None:
        ...

    def consume_event(self, *topics: str) -> AsyncIterator[Event]:
        ...

    def consume_command(self, *topics: str) -> AsyncIterator[Command]:
        ...

    async def close(self) -> None:
        ...

    async def __aenter__(self) -> 'EventQueuePort':
        ...

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        ...
