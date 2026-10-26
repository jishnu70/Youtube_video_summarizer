# app/repo/db.py

import logging
from functools import lru_cache

from sqlalchemy.exc import DBAPIError, SQLAlchemyError
from sqlalchemy.orm import joinedload
from sqlmodel import desc, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.summary import Summary
from app.models.task import Task
from app.models.video import Video

logger = logging.getLogger(__name__)


class DatabaseRepository:
    async def fetch_summary(self, db: AsyncSession, url: str) -> Summary | None:
        """
        Fetches the summary of a video from the database based on its URL.

        Args:
            db (AsyncSession): The database session.
            url (str): The URL of the video.

        Returns:
            Summary | None: The summary of the video if found, otherwise None.
        """
        query = (
            select(Summary)
            .join(Video)
            .where(Video.url == url)
            .order_by(desc(Summary.created_at))
            .limit(1)
        )
        try:
            result = await db.exec(query)
            summary = result.first()
            return summary
        except Exception as e:  # noqa: BLE001
            logger.error(f"Error fetching summary: {e}")
            return None

    async def fetch_task_using_polling_id(
        self, db: AsyncSession, polling_id: str
    ) -> Task | None:
        """
        Fetches the task associated with a video from the database based on its Polling ID.

        Args:
            db (AsyncSession): The database session.
            task_id (str): The ID of the task.

        Returns:
            Task | None: The task associated with the video if found, otherwise None.
        """
        query = (
            select(Task)
            .options(joinedload(Task.summary))  # type: ignore
            .where(Task.polling_id == polling_id)
            .limit(1)
        )
        try:
            result = await db.exec(query)
            task = result.first()
            return task
        except Exception as e:  # noqa: BLE001
            logger.error(f"Error fetching task: {e}")
            return None

    async def fetch_task_using_url(self, db: AsyncSession, url: str) -> Task | None:
        """
        Fetches the task associated with a video from the database based on its URL.

        Args:
            db (AsyncSession): The database session.
            url (str): The URL of the video.

        Returns:
            Task | None: The task associated with the video if found, otherwise None.
        """
        query = (
            select(Task).where(Task.url == url).order_by(desc(Task.created_at)).limit(1)
        )
        try:
            result = await db.exec(query)
            task = result.first()
            return task
        except Exception as e:  # noqa: BLE001
            logger.error(f"Error fetching task by URL: {e}")
            return None

    async def create_task(self, db: AsyncSession, url: str) -> Task | None:
        """
        Creates a new task for a video in the database based on its URL.

        Args:
            db (AsyncSession): The database session.
            url (str): The URL of the video.

        Returns:
            Task | None: The created task if successful, otherwise None.
        """
        task = Task(url=url)
        db.add(task)

        try:
            await db.flush()
            await db.commit()
            await db.refresh(task)
            return task
        except (SQLAlchemyError, DBAPIError) as e:
            logger.error(f"Error committing new task: {e}")
            await db.rollback()
            return None

    async def update_task(self, db: AsyncSession, task: Task) -> Task | None:
        """
        Updates an existing task in the database.

        Args:
            db (AsyncSession): The database session.
            task (Task): The task to be updated.

        Returns:
            Task | None: The updated task if successful, otherwise None.
        """
        try:
            await db.flush()
            await db.commit()
            await db.refresh(task)
            return task
        except (SQLAlchemyError, DBAPIError) as e:
            logger.error(f"Error updating task: {e}")
            await db.rollback()
            return None


@lru_cache
def get_database_repository() -> DatabaseRepository:
    """
    Returns a cached instance of the DatabaseRepository.

    Returns:
        DatabaseRepository: An instance of the DatabaseRepository.
    """
    return DatabaseRepository()
