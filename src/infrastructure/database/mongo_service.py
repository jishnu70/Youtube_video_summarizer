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
        self.client = AsyncIOMotorClient(uri)
        self.db = self.client[db_name]
        self.collection = self.db["videos"]

    async def get_video(self, url: str) -> Optional[dict]:
        """
        Retrieve a video document by URL, returning only the latest summary.
        """
        pipeline = [
            {"$match": {"url": url}},
            {"$project": {
                "url": 1,
                "transcription": 1,
                "created_at": 1,
                "summaries": {
                    "$filter": {
                        "input": "$summaries",
                        "cond": {"$eq": ["$$summaries.latest", True]}
                    }
                }
            }}
        ]
        cursor = self.collection.aggregate(pipeline)
        result = await cursor.to_list(length=1)
        return dict(result) or None

    async def save(self,
        url: str,
        transcription: str,
        summary: str,
        model_name: str="facebook/bart-large-cnn"
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
            await self.collection.update_one(
                {"url": url},
                {"$set": {"summaries.$[].latest": False}}
            )
            await self.collection.update_one(
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
            result = await self.collection.insert_one(doc)
            return str(result.inserted_id)
