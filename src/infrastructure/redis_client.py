# src/infrastructure/redis_client.py

from typing import Optional
from redis.asyncio import Redis
from src.domain.entities import VideoResponse
import redis
from src.infrastructure.system_config import config
import logging
import json

logger = logging.getLogger(__name__)

class RedisClient:
    def __init__(self, url: str) -> None:
        self._redis = Redis.from_url(url)

    async def set_queued_task(self, taskID: str, url: str):
        try:
            await self._redis.set(name=f"queue:{url}", value=taskID)
        except redis.RedisError as re:
            logger.error(f"Redis error while saving taskID for {url}: {re}")
            return None

    async def get_queued_task(self, url: str) -> Optional[str]:
        try:
            taskID = await self._redis.get(f"queue:{url}")
            return taskID
        except redis.RedisError as re:
            logger.error(f"Redis error while fetching taskID for {url}: {re}")
            return None

    async def delete_queued_task(self, url: str):
        try:
            await self._redis.delete(f"queue:{url}")
        except redis.RedisError as re:
            logger.error(f"Redis error while fetching taskID for {url}: {re}")
            return None

    async def get_cached_summary(self, url: str) -> Optional[VideoResponse]:
        try:
            cached = await self._redis.get(f"summary:{url}")
            if cached:
                logger.info(f"Cache hit: {url}")
                return VideoResponse(**json.loads(cached))
            return None
        except redis.RedisError as re:
            logger.error(f"Redis error while fetching cache for {url}: {re}")
            return None

    async def set_cache_summary(self, summary: VideoResponse, exp: int = 3600):
        try:
            await self._redis.setex(f"summary:{summary.url}", exp, summary.model_dump_json())
            logger.info(f"Cached summary for {summary.url}")
        except redis.RedisError as re:
            logger.error(f"Redis error while saving cache for {summary.url}: {re}")
            return None

def get_redis_client():
    return RedisClient(config.REDIS_URL)
