# services/saga_coordinator/app/services/orchestrator.py
import asyncio
from uuid import uuid4, UUID
from datetime import datetime, timezone
from typing import Any, Dict

from libs.messaging.base import Event
from libs.messaging.events import (
    ShipmentCreated,
    ShipmentCancelled,
    InventoryReserved,
    InventoryInsufficient,
    CourierAssigned,
    SagaStarted,
    SagaCompleted,
    SagaFailed,
    SagaCompensating,
    DomainEventConverter,
)
from libs.messaging.commands import (
    ReserveInventoryCommand,
    ReleaseInventoryCommand,
    AssignCourierCommand,
    UnassignCourierCommand,
)
from libs.messaging.ports import EventQueuePort

from src.domain.entities import SagaInstance
from src.domain.ports import SagaRepositoryPort

SHIPMENT_EVENTS_TOPIC = "shipment-events"
INVENTORY_EVENTS_TOPIC = "inventory-events"
DELIVERY_EVENTS_TOPIC = "delivery-events"

INVENTORY_COMMANDS_TOPIC = "inventory-commands"
DELIVERY_COMMANDS_TOPIC = "delivery-commands"
SHIPMENT_EVENTS_OUT_TOPIC = "shipment-events"  # для ShipmentCancelled и т.п.
SAGA_EVENTS_TOPIC = "saga-events"


class ShipmentFulfillmentSagaOrchestrator:
    """
    Оркестратор саги "Shipment Fulfillment":
    ShipmentCreated -> ReserveInventory -> AssignCourier -> Done
    При ошибках: InventoryReleased, CourierUnassigned, SagaFailed.
    """

    def __init__(
        self,
        event_queue: EventQueuePort,
        saga_repo: SagaRepositoryPort,
    ):
        self._queue = event_queue
        self._saga_repo = saga_repo

    async def start(self):
        """
        Запускает три таска-консьюмера по топикам.
        """
        await asyncio.gather(
            self._consume_shipment_events(),
            self._consume_inventory_events(),
            self._consume_delivery_events(),
        )

    async def _consume_shipment_events(self):
        async for event in self._queue.consume_event(SHIPMENT_EVENTS_TOPIC):
            if event.event_type == "shipment.created":
                await self._on_shipment_created(event)

    async def _on_shipment_created(self, event: Event):
        payload = event.payload
        shipment_id = UUID(payload["shipment_id"])
        items = payload.get("items", [])
        warehouse_id = UUID(payload["warehouse_id"]) if "warehouse_id" in payload else UUID(int=0)

        saga_id = uuid4()
        saga = SagaInstance(
            saga_id=saga_id,
            saga_type="ShipmentFulfillment",
            shipment_id=shipment_id,
            warehouse_id=warehouse_id,
        )
        await self._saga_repo.save(saga)

        saga_started = SagaStarted(
            saga_id=saga_id,
            saga_type="ShipmentFulfillment",
            initiated_by="shipment_service",
            started_at=datetime.now(timezone.utc),
        )
        saga_started_event = DomainEventConverter.to_event(saga_started, correlation_id=saga_id)
        await self._queue.publish_event(saga_started_event, topic=SAGA_EVENTS_TOPIC)

        reserve_cmd = ReserveInventoryCommand.create(
            shipment_id=shipment_id,
            warehouse_id=warehouse_id,
            items=items,
            saga_id=saga_id,
        )
        await self._queue.publish_command(reserve_cmd, topic=INVENTORY_COMMANDS_TOPIC)

    async def _consume_inventory_events(self):
        async for event in self._queue.consume_event(INVENTORY_EVENTS_TOPIC):
            if event.event_type == "inventory.reserved":
                await self._on_inventory_reserved(event)
            elif event.event_type == "inventory.insufficient":
                await self._on_inventory_insufficient(event)
            elif event.event_type == "inventory.released":
                pass

    async def _on_inventory_reserved(self, event: Event):
        saga_id = event.correlation_id
        if saga_id is None:
            return

        saga = await self._saga_repo.get(saga_id)
        if saga is None:
            return

        delivery_id = uuid4()
        saga.delivery_id = delivery_id
        saga.updated_at = datetime.now(timezone.utc)
        await self._saga_repo.save(saga)

        assign_cmd = AssignCourierCommand.create(
            shipment_id=saga.shipment_id,
            delivery_id=delivery_id,
            saga_id=saga_id,
        )
        await self._queue.publish_command(assign_cmd, topic=DELIVERY_COMMANDS_TOPIC)

    async def _on_inventory_insufficient(self, event: Event):
        saga_id = event.correlation_id
        if saga_id is None:
            return

        saga = await self._saga_repo.get(saga_id)
        if saga is None:
            return

        saga.mark_failed(step="inventory.reserve", error="inventory_insufficient")
        await self._saga_repo.save(saga)

        payload = event.payload
        shipment_id = UUID(payload["shipment_id"])

        cancelled = ShipmentCancelled(
            shipment_id=shipment_id,
            reason="inventory_insufficient",
            cancelled_at=datetime.now(timezone.utc),
        )
        cancelled_event = DomainEventConverter.to_event(cancelled, correlation_id=saga_id)
        await self._queue.publish_event(cancelled_event, topic=SHIPMENT_EVENTS_OUT_TOPIC)

        saga_failed = SagaFailed(
            saga_id=saga.saga_id,
            saga_type=saga.saga_type,
            error_message="inventory_insufficient",
            failed_at=datetime.now(timezone.utc),
        )
        saga_failed_event = DomainEventConverter.to_event(saga_failed, correlation_id=saga.saga_id)
        await self._queue.publish_event(saga_failed_event, topic=SAGA_EVENTS_TOPIC)

    async def _consume_delivery_events(self):
        async for event in self._queue.consume_event(DELIVERY_EVENTS_TOPIC):
            if event.event_type == "courier.assigned":
                await self._on_courier_assigned(event)
            elif event.event_type == "delivery.failed":
                await self._on_delivery_failed(event)

    async def _on_courier_assigned(self, event: Event):
        saga_id = event.correlation_id
        if saga_id is None:
            return

        saga = await self._saga_repo.get(saga_id)
        if saga is None:
            return

        saga.mark_completed()
        await self._saga_repo.save(saga)

        saga_completed = SagaCompleted(
            saga_id=saga.saga_id,
            saga_type=saga.saga_type,
            completed_at=datetime.now(timezone.utc),
        )
        saga_completed_event = DomainEventConverter.to_event(saga_completed, correlation_id=saga.saga_id)
        await self._queue.publish_event(saga_completed_event, topic=SAGA_EVENTS_TOPIC)

    async def _on_delivery_failed(self, event: Event):
        saga_id = event.correlation_id
        if saga_id is None:
            return

        saga = await self._saga_repo.get(saga_id)
        if saga is None:
            return

        saga.mark_compensating(step="delivery.assign")
        await self._saga_repo.save(saga)

        release_cmd = ReleaseInventoryCommand.create(
            shipment_id=saga.shipment_id,
            warehouse_id=saga.warehouse_id,
            items=[],
            saga_id=saga.saga_id,
            reason="delivery_failed",
        )
        await self._queue.publish_command(release_cmd, topic=INVENTORY_COMMANDS_TOPIC)

        if saga.delivery_id:
            unassign_cmd = UnassignCourierCommand.create(
                delivery_id=saga.delivery_id,
                saga_id=saga.saga_id,
                reason="delivery_failed",
            )
            await self._queue.publish_command(unassign_cmd, topic=DELIVERY_COMMANDS_TOPIC)

        saga_failed = SagaFailed(
            saga_id=saga.saga_id,
            saga_type=saga.saga_type,
            error_message="delivery_failed",
            failed_at=datetime.now(timezone.utc),
        )
        saga_failed_event = DomainEventConverter.to_event(saga_failed, correlation_id=saga.saga_id)
        await self._queue.publish_event(saga_failed_event, topic=SAGA_EVENTS_TOPIC)
