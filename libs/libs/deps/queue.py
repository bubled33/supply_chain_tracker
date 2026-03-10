from typing import AsyncIterator, Optional

from libs.messaging.memory import InMemoryEventQueueAdapter
from libs.messaging.ports import EventQueuePort


class EventQueueProvider:

    def __init__(
            self,
            use_kafka: bool = False,
            bootstrap_servers: str = "localhost:9092",
            group_id: str = "default-service",
            kafka_topic_prefix: str = ""
    ):
        self.use_kafka = use_kafka
        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id
        self.kafka_topic_prefix = kafka_topic_prefix

        self._adapter: Optional[EventQueuePort] = None

    async def __call__(self) -> AsyncIterator[EventQueuePort]:
        if self._adapter is None:
            await self.startup()

        try:
            yield self._adapter
        finally:
            pass

    async def startup(self):
        if self.use_kafka:
            print(f"[INFO] Initializing Kafka EventQueue for {self.group_id}...")
            pass
        else:
            print(f"[INFO] Initializing In-Memory EventQueue for {self.group_id}...")
            self._adapter = InMemoryEventQueueAdapter(
                bootstrap_servers="mock",
                group_id=self.group_id,
            )

        if hasattr(self._adapter, '_get_producer'):
            await self._adapter._get_producer()

    async def shutdown(self):
        if self._adapter:
            print(f"[INFO] Closing EventQueue for {self.group_id}...")
            if hasattr(self._adapter, 'close'):
                await self._adapter.close()
            self._adapter = None

