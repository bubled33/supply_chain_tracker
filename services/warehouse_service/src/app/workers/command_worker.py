import uuid

from libs.messaging.base import Command
from libs.messaging.ports import EventQueuePort
from libs.observability.logger import get_json_logger, set_correlation_id

from src.app.services.inventory_record import InventoryService
from src.domain.entities.inventory_record import InventoryStatus
from src.domain.errors.inventory_record import InventoryRecordNotFoundError

COMMAND_TOPIC = "inventory.commands"


class WarehouseCommandWorker:

    def __init__(self, event_queue: EventQueuePort, inventory_service: InventoryService):
        self.queue = event_queue
        self.service = inventory_service
        self.logger = get_json_logger("warehouse_command_worker")

    async def run(self):
        self.logger.info("Warehouse Command Worker running", extra={"topic": COMMAND_TOPIC})

        async for command in self.queue.consume_command(COMMAND_TOPIC):
            if command.correlation_id:
                set_correlation_id(str(command.correlation_id))

            try:
                await self._handle_command(command)
            except Exception as e:
                self.logger.error(
                    f"Error handling command {command.command_type}",
                    exc_info=e,
                    extra={"command_id": str(command.command_id)},
                )

    async def _handle_command(self, command: Command) -> None:
        self.logger.info(
            "Processing command",
            extra={"command_type": command.command_type, "aggregate_id": str(command.aggregate_id)},
        )

        if command.command_type == "inventory.release":
            await self._handle_release_inventory(command)
        else:
            self.logger.warning(
                "Unknown command type — skipping",
                extra={"command_type": command.command_type},
            )

    async def _handle_release_inventory(self, command: Command) -> None:
        shipment_id_raw = command.payload.get("shipment_id")
        reason = command.payload.get("reason", "Saga compensation")

        if not shipment_id_raw:
            self.logger.error("Missing shipment_id in command payload", extra={"payload": command.payload})
            return

        try:
            shipment_id = uuid.UUID(str(shipment_id_raw))
        except ValueError:
            self.logger.error("Invalid shipment_id in command payload", extra={"payload": command.payload})
            return

        records = await self.service.list_records_by_shipment(shipment_id)

        if not records:
            self.logger.warning(
                "No inventory records found for shipment during compensation",
                extra={"shipment_id": str(shipment_id)},
            )
            return

        released_count = 0
        for record in records:
            try:
                await self.service.update_status(record.record_id, InventoryStatus.RECEIVED)
                released_count += 1
            except InventoryRecordNotFoundError:
                self.logger.warning(
                    "Inventory record not found during compensation",
                    extra={"record_id": str(record.record_id)},
                )
            except Exception as e:
                self.logger.error(
                    "Failed to release inventory record",
                    exc_info=e,
                    extra={"record_id": str(record.record_id)},
                )

        self.logger.info(
            "Inventory released as compensation",
            extra={"shipment_id": str(shipment_id), "released_count": released_count, "reason": reason},
        )
