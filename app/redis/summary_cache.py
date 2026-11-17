# app/redis/summary_cache.py

import asyncio
import json
import logging
from collections.abc import Awaitable, Callable
from functools import lru_cache
from uuid import uuid4

from redis.asyncio import Redis

from app.models.summary import Summary

logger = logging.getLogger(__name__)


class SummaryCache:
    CACHE_PREFIX = "summary_cache:"
    LOCK_PREFIX = "lock:summary:"
    EXPIRATION_TIME = 3600  # 1 hour

    # Lock configuration settings
    LOCK_TTL_MS = 5000  # 5 seconds maximum for a DB fetch to complete
    RETRY_DELAY = 0.05  # Sleep 50ms between cache retries
    MAX_RETRIES = 20  # Stop waiting after ~1 second total (fallback to DB)

    def __init__(self, url: str) -> None:
        if not url:
            raise ValueError("Redis URL must be provided")
        self._redis = Redis.from_url(url)

    def _get_cache_key(self, url: str) -> str:
        """
        Generate a cache key for the given URL.
        """
        return f"{self.CACHE_PREFIX}{url}"

    def _get_lock_key(self, url: str) -> str:
        """
        Generate a lock key for the given URL.
        """
        return f"{self.LOCK_PREFIX}{url}"

    async def get_summary(self, url: str) -> Summary | None:
        """
        Fetches the summary from the cache based on the video URL.
        """
        cache_key = self._get_cache_key(url)
        cached_summary = await self._redis.get(cache_key)
        if cached_summary:
            return Summary.model_validate(json.loads(cached_summary))
        return None

    async def set_summary(self, url: str, summary: Summary) -> bool:
        """
        Caches the summary in Redis with an expiration time.
        """
        if not summary or not url:
            raise ValueError("Summary and its video URL must be provided")
        cache_key = self._get_cache_key(url)
        return await self._redis.set(
            cache_key, summary.model_dump_json(), ex=self.EXPIRATION_TIME
        )

    async def get_or_create(
        self, url: str, db_fetch_callback: Callable[[], Awaitable[Summary | None]]
    ) -> Summary | None:
        """
        Fetches the summary from the cache. If not found, it fetches from the database using the provided callback,
        caches it, and returns it.

        Args:
            url (str): The URL of the video.
            db_fetch_callback (Callable[[], Awaitable[Summary|None]]): A callback function to fetch the summary from the database.

        Returns:
            Summary | None: The summary of the video if found, otherwise None.
        """
        cached_summary = await self.get_summary(url)
        if cached_summary:
            return cached_summary

        lock_key = self._get_lock_key(url)
        lock_token = str(uuid4())
        acquired_lock = await self._redis.set(
            lock_key, lock_token, nx=True, px=self.LOCK_TTL_MS
        )

        if acquired_lock:
            try:
                logger.info(f"Cache miss for URL: {url}. Fetching from DB.")
                summary = await db_fetch_callback()
                if summary:
                    await self.set_summary(url, summary)
                return summary
            finally:
                current_lock_token = await self._redis.get(lock_key)
                if current_lock_token and current_lock_token.decode() == lock_token:
                    await self._redis.delete(lock_key)

        logger.info(f"Waiting for lock release for URL: {url}. Retrying cache fetch.")
        for _ in range(self.MAX_RETRIES):
            await asyncio.sleep(self.RETRY_DELAY)
            cached_summary = await self.get_summary(url)
            if cached_summary:
                return cached_summary

        logger.warning(
            f"Max retries reached for URL: {url}. Fetching from DB without caching."
        )
        summary = await db_fetch_callback()
        if summary:
            await self.set_summary(url, summary)
        return summary


@lru_cache
def get_summary_cache(redis_url: str) -> SummaryCache:
    """
    Returns a cached instance of SummaryCache.
    """
    return SummaryCache(redis_url)
