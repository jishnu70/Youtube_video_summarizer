import logging
from datetime import UTC, datetime, timedelta

from sqlmodel import select

from app.config import get_settings
from app.database import get_async_session
from app.models.task import Task
from app.redis.queue import enque_task, get_queue_pool
from app.redis.task_cache import get_task_cache
from app.utils.constants import TaskStatus

logger = logging.getLogger(__name__)


class TaskMaintenanceService:
    """Requeues tasks left without a live ARQ worker after a bounded timeout."""

    def __init__(self, stale_after: timedelta = timedelta(minutes=35)) -> None:
        self.stale_after = stale_after

    async def requeue_stuck_tasks(self, stale_after: timedelta | None = None) -> None:
        cutoff = datetime.now(UTC) - (stale_after or self.stale_after)
        task_cache = get_task_cache(get_settings().REDIS_URL)
        async for session in get_async_session():
            result = await session.exec(
                select(Task).where(
                    Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS]),
                    Task.updated_at < cutoff,
                )
            )
            tasks = result.all()
            queue = await get_queue_pool()
            for task in tasks:
                job_key = f"arq:job:{task.id}"
                in_progress_key = f"arq:in-progress:{task.id}"
                if await queue.exists(job_key) or await queue.exists(in_progress_key):
                    logger.info(
                        "ARQ job for task %s is still active; skipping", task.id
                    )
                    continue

                task.status = TaskStatus.PENDING
                task.err_message = None
                task.updated_at = datetime.now(UTC)
                await session.commit()
                ok, error = await enque_task(queue, task)
                if not ok:
                    task.status = TaskStatus.FAILED
                    task.err_message = error or "Failed to requeue stale task"
                    logger.error("Could not requeue task %s", task.id)
                    await session.commit()
                await task_cache.set_task(task)
