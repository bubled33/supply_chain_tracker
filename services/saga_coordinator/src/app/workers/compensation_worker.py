from typing import List, Dict
from libs.observability.logger import get_json_logger, set_correlation_id
from libs.messaging.base import Event
from libs.messaging.commands import (
    ReleaseInventoryCommand,
    UnassignCourierCommand,
    CancelShipmentCommand,
)
from src.domain.entities.saga_instance import SagaInstance
from libs.messaging.ports import EventQueuePort
from src.app.services.saga_instance import SagaService


class SagaCompensationWorker:
    """
    Orchestrates the rollback process for distributed transactions.
    Listens for failure events and triggers compensating commands.
    Uses SagaService for state transitions.
    """

    def __init__(
            self,
            event_queue: EventQueuePort,
            saga_service: SagaService
    ):
        self.queue = event_queue
        self.service = saga_service
        self.logger = get_json_logger("saga_compensation_worker")

    async def run(self):
        self.logger.info("Saga Compensation Worker running")

        error_topics = [
            "inventory.insufficient",
            "delivery.failed",
            "courier.unassigned",
        ]

        async for event in self.queue.consume_event(*error_topics):
            if event.correlation_id:
                set_correlation_id(str(event.correlation_id))

            try:
                await self._handle_failure_event(event)
            except Exception as e:
                self.logger.error(
                    f"Error handling event {event.event_type}",
                    exc_info=e,
                    extra={"event_id": str(event.event_id)}
                )

    async def _handle_failure_event(self, event: Event):
        saga_id = event.correlation_id

        if not saga_id:
            self.logger.warning("Skipping event without correlation_id", extra={"event_type": event.event_type})
            return

        saga = await self.service.get(saga_id)
        if not saga:
            self.logger.error("Saga instance not found", extra={"saga_id": str(saga_id)})
            return

        if saga.status.value in ("completed", "compensating", "failed"):
            self.logger.info(
                "Saga already in final or compensating state",
                extra={"status": saga.status.value}
            )
            return

        self.logger.info(
            "Triggering compensation",
            extra={"reason": event.event_type}
        )

        try:
            saga = await self.service.trigger_compensation(
                saga_id=saga.saga_id,
                failed_step=event.event_type
            )
        except ValueError as e:
            self.logger.warning(f"Failed to trigger compensation: {e}")
            return

        await self._execute_compensation_strategy(saga, event)

        await self.service.fail_saga(
            saga_id=saga.saga_id,
            step=event.event_type,
            error_message=f"Compensation triggered by {event.event_type}"
        )

    async def _execute_compensation_strategy(self, saga: SagaInstance, trigger_event: Event):
        event_type = trigger_event.event_type
        payload = trigger_event.payload
        failure_reason = payload.get("reason", f"Triggered by {event_type}")

        if event_type == "delivery.failed":
            await self._compensate_delivery(saga, reason=failure_reason)
            await self._compensate_inventory(saga, reason="Delivery failed rollback")
            await self._compensate_shipment(saga, reason="Delivery failed rollback")

        elif event_type == "courier.unassigned":
            await self._compensate_inventory(saga, reason="Courier unassigned rollback")
            await self._compensate_shipment(saga, reason="Courier unassigned rollback")

        elif event_type == "inventory.insufficient":
            await self._compensate_shipment(saga, reason="Inventory insufficient")

    async def _compensate_inventory(self, saga: SagaInstance, reason: str):
        if not saga.warehouse_id:
            self.logger.warning("Skipping inventory compensation: No warehouse_id")
            return

        items_to_release: List[Dict] = []

        command = ReleaseInventoryCommand.create(
            shipment_id=saga.shipment_id,
            warehouse_id=saga.warehouse_id,
            items=items_to_release,
            saga_id=saga.saga_id,
            reason=reason
        )

        await self.queue.publish_command(command, "inventory.commands")
        self.logger.info("Sent ReleaseInventoryCommand")

    async def _compensate_shipment(self, saga: SagaInstance, reason: str):
        command = CancelShipmentCommand.create(
            shipment_id=saga.shipment_id,
            reason=reason,
            saga_id=saga.saga_id
        )

        await self.queue.publish_command(command, "shipment.commands")
        self.logger.info("Sent CancelShipmentCommand")

    async def _compensate_delivery(self, saga: SagaInstance, reason: str):
        if not saga.delivery_id:
            return

        command = UnassignCourierCommand.create(
            delivery_id=saga.delivery_id,
            saga_id=saga.saga_id,
            reason=reason
        )

        await self.queue.publish_command(command, "delivery.commands")
        self.logger.info("Sent UnassignCourierCommand")
