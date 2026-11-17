# app/redis/task_cache.py

import asyncio
import json
import logging
from collections.abc import Awaitable, Callable
from enum import Enum
from functools import lru_cache
from uuid import uuid4

from redis.asyncio import Redis

from app.models.task import Task

logger = logging.getLogger(__name__)


class TaskCache:
    class Keys(Enum):
        URL_PREFIX = "task:url:"
        POLLING_ID_PREFIX = "task:polling_id:"
        LOCK_SUMMARY_PREFIX = "lock:summary:"
        LOCK_POLLING_ID_PREFIX = "lock:polling_id:"

    EXPIRATION_TIME = 3600
    TRANSIENT_EXPIRATION_TIME = 15

    # Lock configuration settings
    LOCK_TTL_MS = 5000  # 5 seconds maximum for a DB fetch to complete
    RETRY_DELAY = 0.05  # Sleep 50ms between cache retries
    MAX_RETRIES = 20  # Stop waiting after ~1 second total (fallback to DB)

    def __init__(self, url: str) -> None:
        if not url:
            raise ValueError("Redis URL must be provided")
        self._redis = Redis.from_url(url)

    def _get_specific_key(self, *, prefix: Keys, identifier: str) -> str:
        """
        Generate a cache key for the given identifier with a specific prefix.
        """
        return f"{prefix.value}{identifier}"

    def _get_lock_token(self) -> str:
        """
        Generate a unique token for lock ownership.
        """
        return str(uuid4())

    # get_task_by_url
    async def get_task_by_url(self, url: str) -> Task | None:
        """
        Fetches the task from the cache based on the video URL.
        """
        cache_key = self._get_specific_key(prefix=self.Keys.URL_PREFIX, identifier=url)
        cached_task = await self._redis.get(cache_key)
        if cached_task:
            return Task.model_validate(json.loads(cached_task))
        return None

    # get_task_by_polling_id
    async def get_task_by_polling_id(self, polling_id: str) -> Task | None:
        """
        Fetches the task from the cache based on the Polling ID.
        """
        cache_key = self._get_specific_key(
            prefix=self.Keys.POLLING_ID_PREFIX, identifier=polling_id
        )
        cached_task = await self._redis.get(cache_key)
        if cached_task:
            return Task.model_validate(json.loads(cached_task))
        return None

    async def set_task(self, task: Task) -> bool:
        """
        Caches the task in Redis with an expiration time based on both the video URL and Polling ID.

        This avoids the need for two separate calls to set_task_by_url and set_task_by_polling_id,
        ensuring that both cache entries are created atomically.

        Else the request would hit the DB twice, once for the URL and once for the Polling ID.
        """
        if not task or not task.url or not task.polling_id:
            raise ValueError(
                "Task, its associated video URL, and Polling ID must be provided"
            )
        url_cache_key = self._get_specific_key(
            prefix=self.Keys.URL_PREFIX, identifier=task.url
        )
        polling_id_cache_key = self._get_specific_key(
            prefix=self.Keys.POLLING_ID_PREFIX, identifier=task.polling_id
        )

        serialized_task = task.model_dump_json()
        expiration = (
            self.TRANSIENT_EXPIRATION_TIME
            if task.status.value in {"pending", "in_progress"}
            else self.EXPIRATION_TIME
        )
        # Cache by URL
        url_set_result = await self._redis.set(
            url_cache_key, serialized_task, ex=expiration
        )
        # Cache by Polling ID
        polling_id_set_result = await self._redis.set(
            polling_id_cache_key, serialized_task, ex=expiration
        )
        return url_set_result and polling_id_set_result

    # get_or_create_task_atomic_wrapper
    async def _atomic_get_or_create_wrapper(
        self,
        *,
        lock_key: str,
        lock_token: str,
        context_label: str,
        db_fetch_callback: Callable[[], Awaitable[Task | None]],
        cache_callback: Callable[[], Awaitable[Task | None]],
        cache_setter: Callable[[Task], Awaitable[bool]],
    ) -> Task | None:
        """
        A generic atomic wrapper to handle cache fetching and database fallback with locking.

        Args:
            lock_key (str): The Redis key for the lock.
            cache_key (str): The Redis key for the cache.
            context_label (str): A label for logging context.
            db_fetch_callback (Callable): A callback function to fetch the task from the database.
            cache_callback (Callable): A callback function to fetch the task from the cache.
            cache_setter (Callable): A callback function to set the task in the cache.

        Returns:
            Task | None: The task associated with the video if found, otherwise None.
        """
        cached_task = await cache_callback()
        if cached_task:
            return cached_task

        acquired_lock = await self._redis.set(
            lock_key, lock_token, nx=True, px=self.LOCK_TTL_MS
        )

        if acquired_lock:
            try:
                logger.info(f"Cache miss for {context_label}. Fetching from DB.")
                task = await db_fetch_callback()
                if task:
                    await cache_setter(task)
                return task
            finally:
                currently_locked_token = await self._redis.get(lock_key)
                if (
                    currently_locked_token
                    and currently_locked_token.decode() == lock_token
                ):
                    await self._redis.delete(lock_key)

        logger.info(
            f"Waiting for lock release for {context_label}. Retrying cache fetch."
        )
        for _ in range(self.MAX_RETRIES):
            await asyncio.sleep(self.RETRY_DELAY)
            cached_task = await cache_callback()
            if cached_task:
                return cached_task

        logger.warning(
            f"Cache fetch failed after retries for {context_label}. Fetching from DB."
        )
        task = await db_fetch_callback()
        if task:
            await cache_setter(task)
        return task

    async def get_or_create_task_by_url(
        self, url: str, db_fetch_callback: Callable[[], Awaitable[Task | None]]
    ) -> Task | None:
        """
        Fetches the task from the cache based on the video URL. If not found, it fetches from the database using the provided callback,
        caches it, and returns it.

        Args:
            url (str): The URL of the video.
            db_fetch_callback (Callable[[], Awaitable[Task|None]]): A callback function to fetch the task from the database.

        Returns:
            Task | None: The task associated with the video if found, otherwise None.
        """
        lock_key = self._get_specific_key(
            prefix=self.Keys.LOCK_SUMMARY_PREFIX, identifier=url
        )
        lock_token = self._get_lock_token()
        context_label = f"URL: {url}"

        return await self._atomic_get_or_create_wrapper(
            lock_key=lock_key,
            lock_token=lock_token,
            context_label=context_label,
            db_fetch_callback=db_fetch_callback,
            cache_callback=lambda: self.get_task_by_url(url),
            cache_setter=self.set_task,
        )

    async def get_or_create_task_by_polling_id(
        self, polling_id: str, db_fetch_callback: Callable[[], Awaitable[Task | None]]
    ) -> Task | None:
        """
        Fetches the task from the cache based on the Polling ID. If not found, it fetches from the database using the provided callback,
        caches it, and returns it.

        Args:
            polling_id (str): The Polling ID of the task.
            db_fetch_callback (Callable[[], Awaitable[Task|None]]): A callback function to fetch the task from the database.

        Returns:
            Task | None: The task associated with the Polling ID if found, otherwise None.
        """
        lock_key = self._get_specific_key(
            prefix=self.Keys.LOCK_POLLING_ID_PREFIX, identifier=polling_id
        )
        lock_token = self._get_lock_token()
        context_label = f"Polling ID: {polling_id}"

        return await self._atomic_get_or_create_wrapper(
            lock_key=lock_key,
            lock_token=lock_token,
            context_label=context_label,
            db_fetch_callback=db_fetch_callback,
            cache_callback=lambda: self.get_task_by_polling_id(polling_id),
            cache_setter=self.set_task,
        )


@lru_cache
def get_task_cache(redis_url: str) -> TaskCache:
    """
    Returns a cached instance of TaskCache for the given Redis URL.
    """
    return TaskCache(redis_url)
