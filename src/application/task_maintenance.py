# src/application/task_maintenance.py

import logging
from typing import Any, AsyncIterator, Optional

from src.background.celery_app import celery_app
from src.infrastructure.mongo_service import MongoService
from src.infrastructure.redis_client import RedisClient, get_redis_client

logger = logging.getLogger(__name__)


class TaskMaintenanceService:
    def __init__(self, mongo: MongoService, redis_client: Optional[RedisClient] = None):
        self.mongo = mongo
        self.redis = redis_client or get_redis_client()

    async def iter_queued_tasks(self) -> AsyncIterator[dict[str, Any]]:
        """Yield task documents with status QUEUED. MongoService should expose an iterator wrapper."""
        async for doc in self.mongo.iter_tasks_by_status("QUEUED"):
            yield doc

    async def requeue_stuck_tasks(self) -> None:
        """
        Requeue stuck tasks safely:
        - use redis to avoid duplicates
        - use celery_app.AsyncResult to check broker state
        - update mongo via MongoService methods, not direct collection access
        """

        async for doc in self.iter_queued_tasks():
            try:
                if not doc or "video_url" not in doc or "task_id" not in doc:
                    logger.warning(
                        "Invalid task doc, marking INVALID: %s", doc.get("_id")
                    )
                    if id := doc.get("_id"):
                        await self.mongo.mark_task_invalid(id)
                        continue
                    else:
                        logger.error(
                            "Doc missing _id, cannot mark requeue error: %s in mark_task_invalid block",
                            doc,
                        )
                url = doc["video_url"]
                old_task_id = doc["task_id"]

                # Skip if Redis already has queued task for this url
                existing = await self.redis.get_queued_task(url)
                if existing:
                    logger.info(
                        "Redis already has queued task for %s -> %s, skipping",
                        url,
                        existing,
                    )
                    if existing != old_task_id:
                        if id := doc.get("_id"):
                            await self.mongo.update_task_id(id, existing)
                        else:
                            logger.error(
                                "Doc missing _id, cannot mark requeue error: %s in update_task_id block",
                                doc,
                            )
                    continue

                # Check Celery broker state
                res = celery_app.AsyncResult(old_task_id)
                if getattr(res, "state", None) in ("PENDING", "RETRY", "STARTED"):
                    logger.info(
                        "Celery indicates task %s is in %s; skipping",
                        old_task_id,
                        res.state,
                    )
                    continue

                # Send new task
                new_task = celery_app.send_task(
                    "src.application.task_maintenance.requeue_task",
                    args=[url],
                    kwargs={},
                    task_id=old_task_id,  # reuse same task_id to avoid duplicates
                )
                new_task_id = getattr(new_task, "id", None) or str(new_task)

                # Try set redis queued key (set_queued_task should be atomic NX)
                await self.redis.set_queued_task(taskID=new_task_id, url=url)

                # Update mongo task doc to reflect new task id
                if id := doc.get("_id"):
                    await self.mongo.update_task_after_requeue(id, new_task_id)
                else:
                    logger.error(
                        "Doc missing _id, cannot mark requeue error: %s in update_task_after_requeue block",
                        doc,
                    )

                logger.info("Requeued %s as %s", url, new_task_id)

            except Exception as e:
                logger.exception("Failed to requeue doc %s: %s", doc.get("_id"), e)
                # Optionally mark doc as needing manual attention
                try:
                    if id := doc.get("_id"):
                        await self.mongo.mark_task_requeue_error(id)
                    else:
                        logger.error(
                            "Doc missing _id, cannot mark requeue error: %s in exception block",
                            doc,
                        )
                except Exception:
                    logger.exception(
                        "Marking requeue error failed for %s", doc.get("_id")
                    )
