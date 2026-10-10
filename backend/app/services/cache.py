import redis.asyncio as redis
import hashlib
import json
import logging
from typing import Optional, Any

logger = logging.getLogger(__name__)

class RedisCache:
    def __init__(self, url: str):
        self.url = url
        self._client: Optional[redis.Redis] = None

    async def connect(self):
        self._client = redis.from_url(self.url, decode_responses=True)
        try:
            await self._client.ping()
            logger.info("Redis connected")
        except Exception as e:
            logger.warning(f"Redis not available: {e}. Cache disabled.")
            self._client = None

    async def disconnect(self):
        if self._client:
            await self._client.aclose()

    def _make_key(self, prefix: str, text: str) -> str:
        h = hashlib.sha256(text.encode()).hexdigest()
        return f"{prefix}:{h}"

    async def get(self, prefix: str, text: str) -> Optional[Any]:
        if not self._client:
            return None
        try:
            val = await self._client.get(self._make_key(prefix, text))
            return json.loads(val) if val else None
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
            return None

    async def set(self, prefix: str, text: str, value: Any):
        if not self._client:
            return
        try:
            await self._client.set(self._make_key(prefix, text), json.dumps(value))
        except Exception as e:
            logger.warning(f"Cache set error: {e}")
