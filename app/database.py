# app/database.py

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config import get_settings

DATABASE_URL = get_settings().DATABASE_URL

engine: AsyncEngine | None = None
async_session: async_sessionmaker[AsyncSession] | None = None


async def init_db() -> None:
    """
    Initializes the database connection and creates the necessary tables.
    """
    global engine, async_session
    if engine is None:
        engine = create_async_engine(DATABASE_URL, echo=True)
    if async_session is None:
        async_session = async_sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )

    async def _create_tables() -> None:
        async with engine.begin() as conn:  # type: ignore
            await conn.run_sync(SQLModel.metadata.create_all)

    await _create_tables()


async def close_db() -> None:
    """
    Closes the database connection and disposes of the engine.
    """
    if engine:
        await engine.dispose()


async def get_async_session() -> AsyncGenerator[AsyncSession]:
    """
    Provides an asynchronous database session for use in FastAPI routes.
    """
    if async_session is None:
        raise RuntimeError("Database session is not initialized. Call init_db() first.")

    async with async_session() as session:
        yield session
