# src/repo/user_repo.py

from typing import Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection

from src.domain.model_exceptions import RecordNotFoundError
from src.infrastructure.mongo_service import handle_mongo_exception
from src.models.user import UserDB


class UserRepository:
    def __init__(self, collection: AsyncIOMotorCollection):
        self._users = collection

    @handle_mongo_exception
    async def find_user(
        self,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        email: Optional[str] = None,
    ) -> UserDB:
        if not any([user_id is not None, username is not None, email is not None]):
            raise ValueError(
                "At least one of user_id, username, or email must be provided"
            )
        conditions = {"$or": []}
        if user_id:
            id_object = ObjectId(user_id) if ObjectId.is_valid(user_id) else user_id
            conditions["$or"].append({"_id": id_object})
        if username:
            conditions["$or"].append({"username": username})
        if email:
            conditions["$or"].append({"email": email})

        cursor = await self._users.find_one(conditions)
        if cursor is None:
            raise RecordNotFoundError("User not found with the provided identifiers")
        return UserDB(**cursor)

    @handle_mongo_exception
    async def create_user(self, user: UserDB) -> UserDB:
        result = await self._users.insert_one(user.model_dump(by_alias=True))
        user.id = str(result.inserted_id)
        return user
