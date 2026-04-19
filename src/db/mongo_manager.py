# src/db/mongo_manager.py

import asyncio
import logging
from typing import Annotated, Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pydantic import Field
from pymongo.errors import (
    PyMongoError,
)

from src.domain.model_exceptions import DatabaseUnavailableError

logger = logging.getLogger(__name__)


class MongoManager:
    """
    Manages MongoDB connection and provides utility methods for database operations.
    """

    def __init__(self, uri: str, db_name: str) -> None:
        self._uri = uri
        self._db_name = db_name
        self._client: Optional[AsyncIOMotorClient] = None
        self._db_internal: Optional[AsyncIOMotorDatabase] = None
        self._startup_lock = (
            asyncio.Lock()
        )  # lock to ensure connect is only called once
        self._collection = None  # collection for user location data

    async def _connect_internal(self) -> None:
        """Internal method to establish MongoDB connection. Should be called once at startup."""
        async with self._startup_lock:
            if self._client:
                return  # already connected
            try:
                self._client = AsyncIOMotorClient(
                    host=self._uri,
                    serverSelectionTimeoutMS=5000,
                    connectTimeoutMS=5000,
                    socketTimeoutMS=5000,
                )
                self._db_internal = self._client[self._db_name]
                await self.health_check()
                return  # connection successful
            except Exception as e:
                logger.warning(f"Connection failed: {e}")
                self._client = None
                self._db_internal = None
                raise DatabaseUnavailableError(
                    "An unexpected error occurred while connecting to the database."
                ) from e

    async def connect(self) -> None:
        """Establishes the MongoDB connection."""
        await self._connect_internal()

    async def close(self) -> None:
        """Closes the MongoDB connection."""
        if self._client:
            self._client.close()
            self._client = None
            self._db_internal = None

    async def health_check(self) -> bool:
        """Performs a health check by pinging the MongoDB server."""
        if self._client is None:
            return False
        try:
            await self._client.admin.command("ping")
            return True
        except PyMongoError as e:
            logger.error(f"MongoDB health check failed: {e}")
            raise DatabaseUnavailableError() from e

    @property
    def _db(self) -> AsyncIOMotorDatabase:
        """Returns the database instance, ensuring connection is established."""
        if self._db_internal is None:
            raise RuntimeError("Database connection not established")
        return self._db_internal

    def get_collection(self, collection_name: str):
        """Returns a collection from the database."""
        return self._db[collection_name]


MONGO_MANAGER: Annotated[
    Optional[MongoManager], Field(description="Singleton instance of MongoManager")
] = None


def create_mongo_manager(*, uri: str, db_name: str) -> MongoManager:
    """Returns a singleton instance of MongoManager."""
    global MONGO_MANAGER
    if MONGO_MANAGER is None:
        MONGO_MANAGER = MongoManager(uri, db_name)
    return MONGO_MANAGER


def get_mongo_manager() -> MongoManager:
    """Returns the singleton instance of MongoManager, ensuring it is initialized."""
    if MONGO_MANAGER is None:
        raise RuntimeError(
            "MongoManager has not been initialized. Call create_mongo_manager first."
        )
    return MONGO_MANAGER
