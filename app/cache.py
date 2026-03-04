import hashlib

import orjson
import redis.asyncio as aioredis
import structlog

logger = structlog.get_logger()


class CacheLayer:
    def __init__(self, redis_url: str, ttl: int = 3600):
        self._redis: aioredis.Redis | None = None
        self._url = redis_url
        self._ttl = ttl
        self._available = False

    async def connect(self) -> None:
        try:
            self._redis = aioredis.from_url(
                self._url, decode_responses=False, socket_connect_timeout=3
            )
            await self._redis.ping()
            self._available = True
            logger.info("redis_connected")
        except Exception as exc:
            logger.warning("redis_unavailable", error=str(exc))
            self._available = False

    async def close(self) -> None:
        if self._redis:
            await self._redis.aclose()

    @staticmethod
    def _key(sql: str) -> str:
        normalized = " ".join(sql.strip().lower().split())
        digest = hashlib.blake2b(normalized.encode(), digest_size=16).hexdigest()
        return f"duckdb:{digest}"

    async def get(self, sql: str) -> dict | None:
        if not self._available or not self._redis:
            return None
        try:
            data = await self._redis.get(self._key(sql))
            return orjson.loads(data) if data else None
        except Exception:
            self._available = False
            return None

    async def set(self, sql: str, result: dict) -> None:
        if not self._available or not self._redis:
            return
        try:
            await self._redis.set(
                self._key(sql),
                orjson.dumps(result, default=str),
                ex=self._ttl,
            )
        except Exception:
            self._available = False

    async def flush(self) -> int:
        if not self._available or not self._redis:
            return 0
        count = 0
        try:
            async for key in self._redis.scan_iter("duckdb:*"):
                await self._redis.delete(key)
                count += 1
        except Exception:
            pass
        return count

    @property
    def available(self) -> bool:
        return self._available
