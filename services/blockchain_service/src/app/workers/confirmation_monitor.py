import asyncio
import logging

from src.app.services.blockhain import BlockchainService
from src.domain.ports.blockhain_repository import BlockchainRepositoryPort


class ConfirmationMonitor:
    def __init__(
            self,
            service: BlockchainService,
            repository: BlockchainRepositoryPort,
            interval_seconds: int = 15,
            batch_size: int = 50
    ):
        self._service = service
        self._repo = repository
        self._interval = interval_seconds
        self._batch_size = batch_size
        self._logger = logging.getLogger(self.__class__.__name__)
        self._is_running = False

    async def run(self) -> None:
        self._is_running = True
        self._logger.info("Confirmation Monitor started")

        while self._is_running:
            try:
                pending_records = await self._repo.get_pending_records(limit=self._batch_size)

                if not pending_records:
                    await asyncio.sleep(self._interval)
                    continue

                self._logger.debug(f"Checking {len(pending_records)} pending transactions...")

                tasks = [
                    self._service.update_confirmation(record)
                    for record in pending_records
                ]

                await asyncio.gather(*tasks)

            except asyncio.CancelledError:
                self._logger.info("Monitor stopping...")
                break
            except Exception as e:
                self._logger.error(f"Monitor loop failed: {e}", exc_info=True)
                await asyncio.sleep(self._interval)

    async def stop(self) -> None:
        self._is_running = False
