# src/db/base.py

import logging
from typing import Optional, ParamSpec, TypeVar

from motor.motor_asyncio import AsyncIOMotorCollection

from src.db.helper import IndexConfig
from src.infrastructure.mongo_service import handle_mongo_exception

logger = logging.getLogger(__name__)

P = ParamSpec("P")
R = TypeVar("R")


class BaseRepo:
    def __init__(self, collection: AsyncIOMotorCollection):
        self._collection = collection

    @handle_mongo_exception
    async def ensure_indexes(
        self, field_indices: Optional[list[IndexConfig]] = None
    ) -> None:
        if not field_indices:
            return  # No indexes to create

        for config in field_indices:
            index_spec, options = config.to_index_spec()
            await self._collection.create_index(
                index_spec,
                **options,
            )
            logger.info(f"Index '{options.get('name')}' created successfully.")
