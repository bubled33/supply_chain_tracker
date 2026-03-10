import uuid

from libs.messaging.base import Command
from libs.messaging.ports import EventQueuePort
from libs.observability.logger import get_json_logger, set_correlation_id

from src.app.services.delivery import DeliveryService
from src.domain.errors.delivery import DeliveryNotFoundError

COMMAND_TOPIC = "delivery.commands"


class DeliveryCommandWorker:

    def __init__(self, event_queue: EventQueuePort, delivery_service: DeliveryService):
        self.queue = event_queue
        self.service = delivery_service
        self.logger = get_json_logger("delivery_command_worker")

    async def run(self):
        self.logger.info("Delivery Command Worker running", extra={"topic": COMMAND_TOPIC})

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

        if command.command_type == "courier.unassign":
            await self._handle_unassign_courier(command)
        else:
            self.logger.warning(
                "Unknown command type — skipping",
                extra={"command_type": command.command_type},
            )

    async def _handle_unassign_courier(self, command: Command) -> None:
        delivery_id_raw = command.payload.get("delivery_id") or str(command.aggregate_id)
        reason = command.payload.get("reason", "Saga compensation")

        try:
            delivery_id = uuid.UUID(str(delivery_id_raw))
        except ValueError:
            self.logger.error("Invalid delivery_id in command payload", extra={"payload": command.payload})
            return

        try:
            await self.service.delete(delivery_id)
            self.logger.info(
                "Delivery deleted as compensation (courier unassigned)",
                extra={"delivery_id": str(delivery_id), "reason": reason},
            )
        except DeliveryNotFoundError:
            self.logger.warning(
                "Delivery not found during compensation — already deleted?",
                extra={"delivery_id": str(delivery_id)},
            )
