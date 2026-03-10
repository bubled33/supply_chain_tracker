from typing import Protocol, Dict, Any, Optional


class BlockchainGatewayPort(Protocol):
    async def send_transaction(self, payload: Dict[str, Any]) -> str:
        ...

    async def get_receipt(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        ...
