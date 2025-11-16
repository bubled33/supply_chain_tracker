from abc import abstractmethod, ABC
from uuid import UUID


class BlockchainGatewayPort(ABC):
    @abstractmethod
    def record_shipment_status(self, shipment_id: UUID, status: str) -> str:
        """
        Записывает статус shipment на блокчейн.
        Возвращает tx_hash.
        """
        pass