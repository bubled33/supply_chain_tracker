import logging
from redis.asyncio import Redis
from web3 import AsyncWeb3

from src.domain.ports.nonce_manager import NonceManagerPort


class RedisNonceManager(NonceManagerPort):
    def __init__(self, redis: Redis, w3: AsyncWeb3, key_prefix: str = "blockchain:nonce:"):
        self._redis = redis
        self._w3 = w3
        self._prefix = key_prefix
        self._logger = logging.getLogger(self.__class__.__name__)

    def _get_key(self, address: str) -> str:
        return f"{self._prefix}{address.lower()}"

    async def sync_from_chain(self, address: str) -> int:
        """
        Принудительно берет nonce из сети и записывает в Redis.
        Используется при старте сервиса или при ошибке 'Nonce too low'.
        """
        on_chain_nonce = await self._w3.eth.get_transaction_count(address, 'pending')

        key = self._get_key(address)

        await self._redis.set(key, on_chain_nonce - 1)
        self._logger.info(f"Synced nonce for {address} from chain: {on_chain_nonce}")
        return on_chain_nonce

    async def get_next_nonce(self, address: str) -> int:
        key = self._get_key(address)

        try:
            nonce = await self._redis.incr(key)
            return nonce
        except Exception:
            raise
