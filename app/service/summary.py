# app/service/summary.py

from functools import lru_cache

from sqlmodel.ext.asyncio.session import AsyncSession

from app.config import get_settings
from app.models.summary import Summary
from app.redis.summary_cache import SummaryCache, get_summary_cache
from app.repo.db import DatabaseRepository, get_database_repository
from app.utils.exceptions import DataNotFound


class SummaryService:
    def __init__(self, db: DatabaseRepository, cache: SummaryCache):
        self._db = db
        self._cache = cache

    async def fetch_summary(self, session: AsyncSession, url: str) -> Summary:
        async def db_lookup():
            return await self._db.fetch_summary(session, url)

        result = await self._cache.get_or_create(url, db_lookup)
        if result is None:
            raise DataNotFound(f"No summary found for URL: {url}")
        return result


@lru_cache
def get_summary_service() -> SummaryService:
    """
    Returns an instance of SummaryService with a cached DatabaseRepository.
    """
    db = get_database_repository()
    cache = get_summary_cache(get_settings().REDIS_URL)
    return SummaryService(db, cache)
