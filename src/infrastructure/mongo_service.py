# src/infrastructure/mongo_service.py

from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
from typing import Optional

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

    async def connect(self):
        """Test the connection (ping)."""
        try:
            await self._client.admin.command('ping')
            print("Pinged your deployment. You successfully connected to MongoDB!")
        except Exception as e:
            print(f"MongoDB connection error: {e}")

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
            condition = {"$match": {"_id": _id}}

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
    ) -> str:
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
            return str(existing["_id"])
        else:
            doc = {
                "url": url,
                "transcription": transcription,
                "summaries": [summary_entry],
                "created_at": datetime.now(timezone.utc)
            }
            result = await self._collection.insert_one(doc)
            return str(result.inserted_id)
