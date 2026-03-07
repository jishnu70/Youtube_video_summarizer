# src/infrastructure/mongo_service.py

import logging
from datetime import datetime, timezone
from functools import wraps
from typing import Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import DuplicateKeyError, PyMongoError, WriteError

from src.domain.model_exceptions import InsufficientData

logger = logging.getLogger(__name__)


def handle_mongo_exception(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except DuplicateKeyError as e:
            logger.error(f"Duplicate key error in {func.__name__}: {e}")
            return None
        except WriteError as e:
            logger.error(f"Write error in {func.__name__}: {e}")
            return None
        except PyMongoError as e:
            logger.error(f"MongoDB error in {func.__name__}: {e}")
            return None

    return wrapper


class MongoService:
    def __init__(self, uri: str, db_name: str = "yt_summarizer") -> None:
        """
        Connect to MongoDB using Motor.
        uri: MongoDB connection string (local or Atlas cloud).
        db_name: database name (default = yt_summarizer).
        """
        self._client = AsyncIOMotorClient(uri)
        self._db = self._client[db_name]
        self._collection = self._db["videos"]
        self._task = self._db["tasks"]

    async def run_init(self):
        """Initialize indexes"""
        await self._collection.create_index("url", unique=True)
        await self._task.create_index("video_url", unique=True)
        logger.info("Mongo indexes ensured")

    async def connect(self):
        """Test the connection (ping)."""
        try:
            await self._client.admin.command("ping")
            print("Pinged your deployment. You successfully connected to MongoDB!")
        except Exception as e:
            logger.exception(f"MongoDB connection error: {e}")

    def disconnect(self):
        try:
            self._client.close()
        except Exception as e:
            logger.exception(f"MongoDB disconnect error: {e}")

    @handle_mongo_exception
    async def insert_task_status(self, task_id: str, video_url: str):
        if not task_id or not video_url:
            logger.error("Cannot insert task status: missing task_id or video_url")
            raise InsufficientData("Missing the required task_id or video_url")
        await self._task.insert_one(
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
        await self._task.update_one(
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
        return await self._task.find_one(query)

    async def get_video(
        self, url: Optional[str] = None, _id: Optional[str] = None
    ) -> Optional[dict]:
        """
        Retrieve a video document by URL, returning only the latest summary.
        """
        if url is None and _id is None:
            raise InsufficientData("Either url or _id must be provided")
        condition = {}
        if url:
            condition = {"$match": {"url": url}}
        elif _id:
            condition = {"$match": {"_id": ObjectId(_id)}}

        pipeline = [
            condition,
            {
                "$project": {
                    "_id": 1,
                    "url": 1,
                    "transcription": 1,
                    "created_at": 1,
                    "summaries": {
                        "$filter": {
                            "input": "$summaries",
                            "as": "summary",  # <-- define variable
                            "cond": {"$eq": ["$$summary.latest", True]},
                        }
                    },
                }
            },
        ]
        cursor = self._collection.aggregate(pipeline)
        result_list = await cursor.to_list(length=1)
        if not result_list:
            return None
        return result_list[0]

    @handle_mongo_exception
    async def save(
        self,
        url: str,
        transcription: str,
        summary: str,
        model_name: str = "google/flan-t5-large",
    ) -> Optional[dict]:
        """
        Save a new video or add a summary to an existing one.
        """
        existing = await self.get_video(url)
        summary_entry = {
            "summary": summary,
            "model_name": model_name,
            "latest": True,
            "created_at": datetime.now(timezone.utc),
        }

        if existing:
            await self._collection.update_one(
                {"url": url},
                {
                    "$set": {"summaries.$[].latest": False},
                    "$push": {"summaries": summary_entry},
                },
            )

            return await self.get_video(url=url)

        doc = {
            "url": url,
            "transcription": transcription,
            "summaries": [summary_entry],
            "created_at": datetime.now(timezone.utc),
        }
        result = await self._collection.insert_one(doc)
        if result_obj := await self.get_video(_id=str(result.inserted_id)):
            return result_obj
        return {
            "_id": str(result.inserted_id),
            "url": url,
            "transcription": transcription,
            "summaries": [summary_entry],
            "created_at": datetime.now(timezone.utc),
        }
