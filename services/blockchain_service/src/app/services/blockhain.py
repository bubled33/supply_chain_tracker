import logging
from datetime import datetime
from typing import Dict
from uuid import UUID

from libs.messaging.events import DomainEventConverter, BlockchainVerified
from libs.messaging.ports import EventQueuePort

from src.domain.entities.blockhain_record import BlockchainRecord, TransactionStatus
from src.domain.ports.blockhain_gateway import BlockchainGatewayPort
from src.domain.ports.blockhain_repository import BlockchainRepositoryPort


class BlockchainService:
    def __init__(
            self,
            repository: BlockchainRepositoryPort,
            gateway: BlockchainGatewayPort,
            queue: EventQueuePort,
            required_confirmations: int = 6
    ):
        self._repo = repository
        self._gateway = gateway
        self._queue = queue
        self._required_confirmations = required_confirmations
        self._logger = logging.getLogger(self.__class__.__name__)

    async def register_event(self, shipment_id: UUID, payload: Dict) -> str:
        tx_hash = await self._gateway.send_transaction(payload)

        record = BlockchainRecord(
            shipment_id=shipment_id,
            tx_hash=tx_hash,
            payload=payload,
            status=TransactionStatus.PENDING
        )

        await self._repo.save(record)
        self._logger.info(f"Saved pending transaction {tx_hash} for {shipment_id}")

        return tx_hash

    async def update_confirmation(self, record: BlockchainRecord) -> None:
        try:
            receipt = await self._gateway.get_receipt(record.tx_hash)

            if not receipt:
                return

            confirmations = receipt.get("confirmations", 0)
            status_on_chain = receipt.get("status")

            if status_on_chain == "failed":
                await self._fail_transaction(record, "Transaction reverted on chain")

            elif status_on_chain == "success":
                if confirmations >= self._required_confirmations:
                    await self._confirm_transaction(record, receipt)
                else:
                    self._logger.debug(
                        f"Tx {record.tx_hash} waiting for confirms: {confirmations}/{self._required_confirmations}"
                    )

        except Exception as e:
            self._logger.error(f"Error updating confirmation for {record.tx_hash}: {e}")

    async def _confirm_transaction(self, record: BlockchainRecord, receipt: dict) -> None:
        record.confirm(
            block_number=receipt["block_number"],
            gas_used=receipt["gas_used"],
            timestamp=datetime.fromisoformat(receipt["timestamp"])
        )

        await self._repo.save(record)

        event = BlockchainVerified(
            record_id=record.record_id,
            shipment_id=record.shipment_id,
            transaction_hash=record.tx_hash,
            verified_at=record.confirmed_at,
            confirmations=self._required_confirmations
        )

        kafka_event = DomainEventConverter.to_event(event)
        await self._queue.publish_event(kafka_event, "blockchain_events")

        self._logger.info(f"Transaction verified: {record.tx_hash}")

    async def _fail_transaction(self, record: BlockchainRecord, reason: str) -> None:
        record.fail(reason)
        await self._repo.save(record)
        self._logger.warning(f"Transaction failed: {record.tx_hash}. Reason: {reason}")
