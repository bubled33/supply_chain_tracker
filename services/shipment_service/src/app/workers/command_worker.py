import uuid

from libs.messaging.base import Command
from libs.messaging.ports import EventQueuePort
from libs.observability.logger import get_json_logger, set_correlation_id

from src.app.services.shipment import ShipmentService
from src.domain.errors import ShipmentNotFoundError

COMMAND_TOPIC = "shipment.commands"


class ShipmentCommandWorker:

    def __init__(self, event_queue: EventQueuePort, shipment_service: ShipmentService):
        self.queue = event_queue
        self.service = shipment_service
        self.logger = get_json_logger("shipment_command_worker")

    async def run(self):
        self.logger.info("Shipment Command Worker running", extra={"topic": COMMAND_TOPIC})

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

        if command.command_type == "shipment.cancel":
            await self._handle_cancel_shipment(command)
        else:
            self.logger.warning(
                "Unknown command type — skipping",
                extra={"command_type": command.command_type},
            )

    async def _handle_cancel_shipment(self, command: Command) -> None:
        shipment_id_raw = command.payload.get("shipment_id") or str(command.aggregate_id)
        reason = command.payload.get("reason", "Saga compensation")

        try:
            shipment_id = uuid.UUID(str(shipment_id_raw))
        except ValueError:
            self.logger.error("Invalid shipment_id in command payload", extra={"payload": command.payload})
            return

        try:
            await self.service.delete(shipment_id)
            self.logger.info(
                "Shipment cancelled (deleted) as compensation",
                extra={"shipment_id": str(shipment_id), "reason": reason},
            )
        except ShipmentNotFoundError:
            self.logger.warning(
                "Shipment not found during compensation — already deleted?",
                extra={"shipment_id": str(shipment_id)},
            )
