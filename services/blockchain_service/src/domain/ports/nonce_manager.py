from asyncio import Protocol


class NonceManagerPort(Protocol):
    async def get_next_nonce(self, address: str) -> int:
        """Получить следующий nonce для адреса (атомарный инкремент)"""
        ...

    async def sync_from_chain(self, address: str) -> int:
        """Синхронизировать nonce с блокчейна (сброс счетчика)"""
        ...