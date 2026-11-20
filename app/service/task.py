# app/service/task.py

import logging
from datetime import UTC, datetime
from functools import lru_cache

from sqlmodel.ext.asyncio.session import AsyncSession

from app.config import get_settings
from app.models.task import Task
from app.redis.queue import enque_task, get_queue_pool
from app.redis.task_cache import TaskCache, get_task_cache
from app.repo.db import DatabaseRepository, get_database_repository
from app.utils.constants import TaskStatus
from app.utils.exceptions import DataNotCreated, DataNotFound

logger = logging.getLogger(__name__)


class TaskService:
    def __init__(self, db: DatabaseRepository, cache: TaskCache):
        self._db: DatabaseRepository = db
        self._cache: TaskCache = cache

    async def fetch_task_using_polling_id(
        self, session: AsyncSession, polling_id: str
    ) -> Task:
        """
        Fetches a task from the database based on its ID.

        Args:
            session (AsyncSession): The database session.
            task_id (str): The ID of the task.

        Returns:
            Task: The task associated with the video.
        """

        async def db_lookup():
            return await self._db.fetch_task_using_polling_id(session, polling_id)

        result = await self._cache.get_or_create_task_by_polling_id(
            polling_id, db_lookup
        )
        if result is None:
            raise DataNotFound(f"No task found for ID: {polling_id}")
        return result

    async def fetch_task_using_url(self, session: AsyncSession, url: str) -> Task:
        """
        Fetches a task from the database based on its URL.

        Args:
            session (AsyncSession): The database session.
            url (str): The URL of the video.

        Returns:
            Task: The task associated with the video.
        """

        async def db_lookup():
            return await self._db.fetch_task_using_url(session, url)

        result = await self._cache.get_or_create_task_by_url(url, db_lookup)
        if result is None:
            raise DataNotFound(f"No task found for URL: {url}")
        return result

    async def get_or_create_task(self, session: AsyncSession, url: str) -> Task:
        """
        Fetches a task from the database based on its URL. If the task does not exist, it creates a new one.

        Args:
            session (AsyncSession): The database session.
            url (str): The URL of the video.

        Returns:
            Task: The task associated with the video.
        """
        try:
            task = await self.fetch_task_using_url(session, url)
        except DataNotFound:
            task = await self._db.create_task(session, url)
            if task is None:
                raise DataNotCreated(f"Failed to create task for URL: {url}")
            await self._cache.set_task(task)
        else:
            if task.status != TaskStatus.FAILED:
                return task
            task.status = TaskStatus.PENDING
            task.err_message = None
            task.updated_at = datetime.now(UTC)
            task = await self._db.update_task(session, task) or task
            await self._cache.set_task(task)

        try:
            queue_pool = await get_queue_pool()
            is_enqueued, err = await enque_task(queue_pool, task)
            if not is_enqueued:
                logger.warning("Broker rejected task %s", task.id)
                task.status = TaskStatus.FAILED
                task.err_message = err or "Broker rejected task"
                task = await self._db.update_task(session, task) or task
                await self._cache.set_task(task)
        except Exception as broker_down_fatal:
            logger.critical(
                "Broker dispatch failed for task %s: %s",
                task.id,
                broker_down_fatal,
                exc_info=True,
            )
            task.status = TaskStatus.FAILED
            task.err_message = (
                f"Background processing engine offline: {broker_down_fatal}"
            )
            task = await self._db.update_task(session, task) or task
            await self._cache.set_task(task)
        return task


@lru_cache
def get_task_service() -> TaskService:
    """
    Returns an instance of TaskService with a cached DatabaseRepository.
    """
    db = get_database_repository()
    cache = get_task_cache(get_settings().REDIS_URL)
    return TaskService(db, cache)
