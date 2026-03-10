import asyncpg
from typing import Optional

class PostgresPoolProvider:

    def __init__(
            self,
            dsn: str,
            min_size: int = 5,
            max_size: int = 20,
            command_timeout: float = 60.0
    ):
        self.dsn = dsn
        self.min_size = min_size
        self.max_size = max_size
        self.command_timeout = command_timeout
        self._pool: Optional[asyncpg.Pool] = None

    async def startup(self):
        if self._pool is None:
            print(f"[INFO] Creating PostgreSQL pool for {self._sanitized_dsn}...")
            self._pool = await asyncpg.create_pool(
                dsn=self.dsn,
                min_size=self.min_size,
                max_size=self.max_size,
                command_timeout=self.command_timeout,
            )

    async def shutdown(self):
        if self._pool is not None:
            print("[INFO] Closing PostgreSQL pool...")
            await self._pool.close()
            self._pool = None

    async def __call__(self) -> asyncpg.Pool:
        if self._pool is None:
            await self.startup()
        return self._pool

    @property
    def _sanitized_dsn(self) -> str:
        try:
            part1, part2 = self.dsn.split("@")
            return f"***@{part2}"
        except ValueError:
            return "DSN"
