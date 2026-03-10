import logging
from typing import List
from uuid import UUID

from libs.messaging.ports import EventQueuePort
from libs.observability.logger import set_correlation_id

from src.app.services.blockhain import BlockchainService


class BlockchainWorker:
    def __init__(
            self,
            queue: EventQueuePort,
            service: BlockchainService,
            listen_topics: List[str],
            target_events: List[str]
    ):
        self._queue = queue
        self._service = service
        self._listen_topics = listen_topics
        self._target_events = target_events
        self._logger = logging.getLogger(self.__class__.__name__)

    async def run(self) -> None:
        self._logger.info("Blockchain worker started")

        async for event in self._queue.consume_event(*self._listen_topics):
            if event.correlation_id:
                set_correlation_id(str(event.correlation_id))

            if event.event_type not in self._target_events:
                continue

            try:
                self._logger.info(f"Processing event: {event.event_type}")

                await self._service.register_event(
                    shipment_id=UUID(event.aggregate_id),
                    payload=event.payload
                )
            except Exception as e:
                self._logger.error(f"Error processing event {event.event_type}: {e}", exc_info=True)
