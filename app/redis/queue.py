# app/redis/queue.py

import logging
from urllib.parse import urlparse

from arq.connections import ArqRedis, RedisSettings, create_pool

from app.config import get_settings
from app.models.task import Task

logger = logging.getLogger(__name__)

_arq_pool: ArqRedis | None = None


async def get_queue_pool() -> ArqRedis:
    """
    Returns a Redis connection pool for the task queue.
    If the pool is not already created, it initializes it.
    """
    global _arq_pool
    if _arq_pool is not None:
        return _arq_pool

    settings = get_settings()

    try:
        prased_url = urlparse(settings.REDIS_URL)

        redis_settings = RedisSettings(
            host=prased_url.hostname or "localhost",
            port=prased_url.port or 6379,
            password=prased_url.password,
            ssl=prased_url.scheme == "rediss",
            conn_timeout=5,
        )

        _arq_pool = await create_pool(redis_settings)
        return _arq_pool
    except Exception as e:
        logger.error(f"Failed to create Redis connection pool: {e}")
        raise


async def enque_task(queue: ArqRedis, task: Task) -> tuple[bool, str | None]:
    """
    Enqueue a task to the Redis queue.
    """
    try:
        await queue.delete(f"arq:result:{task.id}", f"arq:job:{task.id}")
        job = await queue.enqueue_job(
            "process_video_summary_job",
            task_id=str(task.id),
            video_url=task.url,
            _job_id=str(task.id),
        )
        if job is None:
            return (False, f"ARQ deduplicated/rejected job for Task {task.id}")
        return (True, None)
    except Exception as queue_err:
        logger.critical(
            f"Broker dispatch error caught for Task {task.id}. Execution preserved. Error: {queue_err}",
            exc_info=True,
        )
        return (False, str(queue_err))
