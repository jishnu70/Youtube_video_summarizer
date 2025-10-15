# src/presentation/container.py

from fastapi import Request
from src.background.celery_task import queue_yt_video
from src.infrastructure.mongo_service import MongoService
from src.application.use_case import UseCase
import logging

logger = logging.getLogger(__name__)

async def get_use_case(request: Request) -> UseCase:
    """Return the already initialized UseCase instance from app.state."""
    return request.app.state.use_case

async def requeue_stuck_tasks(mongo: MongoService):
    stuck = mongo._task.find({"status": "QUEUED"})
    async for doc in stuck:
        if "video_url" not in doc or "task_id" not in doc:
            logger.error(f"Skipping invalid document missing video_url or task_id: {doc.get('_id')}")
            continue
        url = doc["video_url"]
        task_id = doc["task_id"]
        # Check if actually present in Redis broker
        task = queue_yt_video.AsyncResult(task_id)
        if task.state in ["PENDING", "RETRY"]:
            continue  # still in broker
        # else, requeue
        new_task = queue_yt_video.delay(url)
        await mongo.update_status(new_task.id, "QUEUED")
        await mongo._task.delete_one({"_id": doc["_id"]})
