# src/repo/task_repo.py

import logging
from datetime import datetime, timezone
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorCollection

from src.domain.model_exceptions import InsufficientData
from src.infrastructure.mongo_service import handle_mongo_exception

logger = logging.getLogger(__name__)


class TaskRepository:
    def __init__(self, collection: AsyncIOMotorCollection):
        self._tasks = collection

    @handle_mongo_exception
    async def insert_task_status(self, task_id: str, video_url: str):
        if not task_id or not video_url:
            logger.error("Cannot insert task status: missing task_id or video_url")
            raise InsufficientData("Missing the required task_id or video_url")
        await self._tasks.insert_one(
            {
                "task_id": task_id,
                "video_url": video_url,
                "status": "QUEUED",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            }
        )

    @handle_mongo_exception
    async def update_status(self, task_id: str, status: str):
        await self._tasks.update_one(
            {"task_id": task_id},
            {
                "$set": {
                    "status": status,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
            upsert=True,
        )

    async def get_status(
        self, task_id: Optional[str], video_url: Optional[str]
    ) -> Optional[dict]:
        if not task_id and not video_url:
            logger.error("Get Status ERROR: missing both task_id and video_url")
            raise InsufficientData("Insufficient Data provided")
        query = {}
        if task_id:
            query["task_id"] = task_id
        if video_url:
            query["video_url"] = video_url
        return await self._tasks.find_one(query)
