from typing import AsyncIterator, Optional

from libs.messaging.memory import InMemoryEventQueueAdapter
# Импорты из вашей библиотеки (предполагаемые пути)
from libs.messaging.ports import EventQueuePort


# from messaging.adapters.kafka import KafkaEventQueueAdapter # Раскомментировать, когда появится


class EventQueueProvider:
    """
    Настраиваемый провайдер для EventQueue.
    Может использоваться как Dependency в FastAPI.
    Реализует паттерн Singleton для адаптера (один коннект на приложение).
    """

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

        # Внутреннее хранилище для синглтона
        self._adapter: Optional[EventQueuePort] = None

    async def __call__(self) -> AsyncIterator[EventQueuePort]:
        """
        Метод, который вызывается FastAPI при внедрении зависимости.
        Depends(provider_instance)
        """
        # Lazy initialization (создаем адаптер при первом вызове)
        if self._adapter is None:
            await self.startup()

        try:
            yield self._adapter
        finally:
            # Здесь мы НЕ закрываем соединение, так как хотим переиспользовать его
            # между запросами (Singleton).
            # Закрытие должно происходить при остановке приложения (shutdown).
            pass

    async def startup(self):
        """Явная инициализация (можно вызвать в lifespan startup)"""
        if self.use_kafka:
            # Здесь будет инициализация Kafka адаптера
            # self._adapter = KafkaEventQueueAdapter(
            #     bootstrap_servers=self.bootstrap_servers,
            #     group_id=self.group_id
            # )
            print(f"[INFO] Initializing Kafka EventQueue for {self.group_id}...")
            pass
        else:
            print(f"[INFO] Initializing In-Memory EventQueue for {self.group_id}...")
            self._adapter = InMemoryEventQueueAdapter(
                bootstrap_servers="mock",
                group_id=self.group_id,
            )

        # Если у адаптера есть метод для старта/коннекта (например, init producer)
        if hasattr(self._adapter, '_get_producer'):
            await self._adapter._get_producer()

    async def shutdown(self):
        """Закрытие соединений (вызвать в lifespan shutdown)"""
        if self._adapter:
            print(f"[INFO] Closing EventQueue for {self.group_id}...")
            # Если у адаптера есть метод close
            if hasattr(self._adapter, 'close'):
                await self._adapter.close()
            self._adapter = None

