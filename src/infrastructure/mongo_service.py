# src/infrastructure/mongo_service.py

import asyncio
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
from typing import Optional
import logging

from src.domain.entities import VideoResponse
from src.domain.model_exceptions import InsufficientData

logger = logging.getLogger(__name__)

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
            await self._client.admin.command('ping')
            print("Pinged your deployment. You successfully connected to MongoDB!")
        except Exception as e:
            logger.exception(f"MongoDB connection error: {e}")

    def disconnect(self):
        try:
            self._client.close()
        except Exception as e:
            logger.exception(f"MongoDB disconnect error: {e}")

    async def insert_task_status(self, requestID: str, video_url: str):
        await self._task.insert_one({
            "task_id": requestID,
            "video_url": video_url,
            "status": "QUEUED",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        })

    async def update_status(self, requestID: str, status: str):
        await self._task.update_one(
            {"task_id": requestID},
            {
                "$set": {
                    "status": status,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
            upsert=True,
        )

    async def get_status(self, requestID: Optional[str], video_url: Optional[str]) -> Optional[dict]:
        query = {}
        if requestID:
            query = {"task_id": requestID}
        elif video_url:
            query = {"video_url": video_url}
        else:
            logger.error("Get Status ERROR: missing both requestID and video_url")
            raise InsufficientData("Insufficient Data provided")
        return await self._task.find_one(query)

    async def get_video(self, url: Optional[str] = None, _id: Optional[str] = None) -> Optional[dict]:
        """
        Retrieve a video document by URL, returning only the latest summary.
        """
        if url is None and _id is None:
            raise
        condition = {}
        if url:
            condition = {"$match": {"url": url}}
        elif _id:
            condition = {"$match": {"_id": ObjectId(_id)}}

        pipeline = [
            condition,
            {"$project": {
                "_id": 1,
                "url": 1,
                "transcription": 1,
                "created_at": 1,
                "summaries": {
                    "$filter": {
                        "input": "$summaries",
                        "as": "summary",          # <-- define variable
                        "cond": {"$eq": ["$$summary.latest", True]}
                    }
                }
            }}
        ]
        cursor = self._collection.aggregate(pipeline)
        result_list = await cursor.to_list(length=1)
        if not result_list:
            return None
        return result_list[0]

    async def save(self,
        url: str,
        transcription: str,
        summary: str,
        model_name: str="google/flan-t5-large"
    ) -> dict:
        """
        Save a new video or add a summary to an existing one.
        """
        existing = await self.get_video(url)
        summary_entry = {
            "summary": summary,
            "model_name": model_name,
            "latest": True,
            "created_at": datetime.now(timezone.utc)
        }

        if existing:
            await self._collection.update_one(
                {"url": url},
                {"$set": {"summaries.$[].latest": False}}
            )
            await self._collection.update_one(
                {"url": url},
                {"$push": {"summaries": summary_entry}}
            )
            if result_obj := await self.get_video(_id=str(existing["_id"])):
                return result_obj
        else:
            doc = {
                "url": url,
                "transcription": transcription,
                "summaries": [summary_entry],
                "created_at": datetime.now(timezone.utc)
            }
            result = await self._collection.insert_one(doc)
            if result_obj := await self.get_video(_id=str(result.inserted_id)):
                return result_obj
            return {
                "_id": str(result.inserted_id),
                "url": url,
                "transcription": transcription,
                "summaries": [summary_entry],
                "created_at": datetime.now(timezone.utc)
            }
