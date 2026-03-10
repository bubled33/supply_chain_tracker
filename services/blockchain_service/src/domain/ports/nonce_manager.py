from asyncio import Protocol


class NonceManagerPort(Protocol):
    async def get_next_nonce(self, address: str) -> int:
        ...

    async def sync_from_chain(self, address: str) -> int:
        ...