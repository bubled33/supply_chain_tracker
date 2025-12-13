from typing import Dict, Any, Optional
from datetime import datetime

from src.domain.ports.blockhain_gateway import BlockchainGatewayPort


class MockBlockchainGateway(BlockchainGatewayPort):
    async def send_transaction(self, payload: Dict[str, Any]) -> str:
        return f"0xmock{hash(str(payload)) & 0xFFFFFFFF:x}"

    async def get_receipt(self, tx_hash: str) -> Optional[Dict[str, Any]]:
        return {
            "block_number": 123456,
            "confirmations": 6,
            "timestamp": datetime.utcnow().isoformat(),
        }
