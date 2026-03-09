# src/infrastructure/redis_client.py

import json
import logging
from typing import Optional

import redis
from redis.asyncio import Redis

from src.domain.entities import VideoResponse
from src.infrastructure.system_config import config

logger = logging.getLogger(__name__)

_redis_client_instance: Optional["RedisClient"] = None


class RedisClient:
    def __init__(self, url: str) -> None:
        self._redis = Redis.from_url(url)

    async def set_queued_task(self, taskID: str, url: str, exp: int = 3600) -> bool:
        """
        Atomically set a queued task key only if not already set (NX).
        Returns True if the key was set (we claimed the queue), False if the key already exists or on error.
        """
        try:
            res = await self._redis.set(
                name=f"queue:{url}", value=taskID, nx=True, ex=exp
            )
            if res:
                logger.info(f"Queued taskID {taskID} for {url}")
                return True
            else:
                logger.info(f"Task for {url} is already queued by another worker")
                return False
        except redis.RedisError as re:
            logger.error(f"Redis error while saving taskID for {url}: {re}")
            return False

    async def get_queued_task(self, url: str) -> Optional[str]:
        """
        Get queued task id for URL. Returns str if found, otherwise None.
        """
        try:
            taskID = await self._redis.get(f"queue:{url}")
            if taskID is None:
                logger.info(f"No queued task for {url}")
                return None
            if isinstance(taskID, bytes):
                taskID = taskID.decode("utf-8")
            return str(taskID)
        except redis.RedisError as re:
            logger.error(f"Redis error while fetching taskID for {url}: {re}")
            return None

    async def delete_queued_task(self, url: str) -> bool:
        """
        Delete a queued key. Returns True if deleted (count>0), False otherwise.
        """
        try:
            res = await self._redis.delete(f"queue:{url}")
            if res:
                logger.info(f"Deleted queued task for {url}")
                return True
            else:
                logger.info(f"No queued task to delete for {url}")
                return False
        except redis.RedisError as re:
            logger.error(f"Redis error while fetching taskID for {url}: {re}")
            return False

    async def get_cached_summary(self, url: str) -> Optional[VideoResponse]:
        """
        Get a cached summary. Returns a VideoResponse (Pydantic) or None.
        """
        try:
            cached = await self._redis.get(f"summary:{url}")
            if not cached:
                logger.info(f"No cache found for {url}")
                return None
            if isinstance(cached, bytes):
                cached = cached.decode("utf-8")
            try:
                data = json.loads(cached)
                summary = VideoResponse.model_validate(data)
                logger.info(f"Cache hit for {url}")
                return summary
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Error decoding cache for {url}: {e}")
                return None
        except redis.RedisError as re:
            logger.error(f"Redis error while fetching cache for {url}: {re}")
            return None

    async def set_cache_summary(self, summary: VideoResponse, exp: int = 3600) -> bool:
        """
        Cache the VideoResponse JSON with TTL. Returns True on success, False otherwise.
        """
        try:
            payload = summary.model_dump_json()
            await self._redis.setex(f"summary:{summary.url}", exp, payload)
            logger.info(f"Cached summary for {summary.url}")
            return True
        except redis.RedisError as re:
            logger.error(f"Redis error while saving cache for {summary.url}: {re}")
            return False
        except Exception as e:
            logger.exception(
                "Unexpected error while saving cache for %s: %s", summary.url, e
            )
            return False

    async def close(self):
        """Close the redis connection"""
        try:
            await self._redis.close()
        except Exception as e:
            logger.exception("Error closing redis connection: %s", e)


def get_redis_client() -> RedisClient:
    """Return a RedisClient singleton instance"""
    global _redis_client_instance
    if _redis_client_instance is None:
        _redis_client_instance = RedisClient(config.REDIS_URL)
    return _redis_client_instance
