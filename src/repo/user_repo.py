# src/repo/user_repo.py

import enum
import logging
from functools import lru_cache
from typing import Annotated, Optional

from bson import ObjectId
from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorCollection

from src.db.base import BaseRepo
from src.db.helper import IndexConfig
from src.db.mongo_manager import MongoManager, get_mongo_manager
from src.infrastructure.mongo_service import handle_mongo_exception
from src.models.user import UserDB

logger = logging.getLogger(__name__)


class UNIQUE_KEYS(enum.Enum):
    ID = "_id"
    USERNAME = "username"
    EMAIL = "email"
    PROVIDER = "provider"
    PROVIDER_USER_ID = "provider.user_id"


class UserRepository(BaseRepo):
    def __init__(self, collection: AsyncIOMotorCollection):
        self._users = collection

    async def create_indexes(self):
        await super().ensure_indexes(
            [
                IndexConfig(
                    key="_id",
                    order=1,
                    unique=True,
                    index_name="unique_id",
                ),
                IndexConfig(
                    key="username",
                    order=1,
                    unique=True,
                    index_name="unique_username",
                ),
                IndexConfig(
                    key="email",
                    order=1,
                    unique=True,
                    index_name="unique_email",
                ),
                IndexConfig(
                    key="provider.name",
                    order=1,
                    unique=False,
                    index_name="provider_name",
                ),
                IndexConfig(
                    key="provider.user_id",
                    order=1,
                    unique=True,
                    sparse=True,
                    index_name="unique_provider_user_id",
                ),
            ]
        )

    @handle_mongo_exception
    async def _get_user_by_unique(
        self, *, key: UNIQUE_KEYS, value: str
    ) -> Optional[UserDB]:
        if key == UNIQUE_KEYS.PROVIDER_USER_ID:
            provider_name, provider_user_id = value.split(":", 1)
            condition = {
                "provider.name": provider_name,
                key.value: provider_user_id,
            }
        else:
            condition = {
                key.value: ObjectId(value)
                if key == UNIQUE_KEYS.ID and ObjectId.is_valid(value)
                else value
            }
        result = await self._users.find_one(condition)
        return UserDB.from_db(result) if result else None

    @handle_mongo_exception
    async def user_by_provider_id(self, id: str) -> Optional[UserDB]:
        return await self._get_user_by_unique(
            key=UNIQUE_KEYS.PROVIDER_USER_ID, value=id
        )

    @handle_mongo_exception
    async def user_by_id(self, id: str) -> Optional[UserDB]:
        return await self._get_user_by_unique(key=UNIQUE_KEYS.ID, value=id)

    @handle_mongo_exception
    async def user_by_username(self, username: str) -> Optional[UserDB]:
        return await self._get_user_by_unique(key=UNIQUE_KEYS.USERNAME, value=username)

    @handle_mongo_exception
    async def user_by_email(self, email: str) -> Optional[UserDB]:
        return await self._get_user_by_unique(key=UNIQUE_KEYS.EMAIL, value=email)

    @handle_mongo_exception
    async def find_or_create_user(
        self,
        user_obj: UserDB,
    ) -> UserDB:
        if not user_obj.provider:
            logger.error("Provider information is required for find_or_create_user")
            raise ValueError("Provider information is required for find_or_create_user")
        result = await self._users.find_one_and_update(
            {
                "provider.name": user_obj.provider.name,
                "provider.user_id": user_obj.provider.user_id,
            },
            {"$setOnInsert": user_obj.model_dump(by_alias=True)},
            upsert=True,
            return_document=True,
        )
        return UserDB.from_db(result)

    @handle_mongo_exception
    async def create_user(self, user: UserDB) -> UserDB:
        result = await self._users.insert_one(user.model_dump(by_alias=True))
        user.id = str(result.inserted_id)
        return user


@lru_cache(maxsize=1)
def get_user_repo(mongoManager: Annotated[MongoManager, Depends(get_mongo_manager)]):
    return UserRepository(collection=mongoManager.get_collection("users"))
