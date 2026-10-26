# app/config.py

from functools import lru_cache
from typing import Annotated

from pydantic import Field
from pydantic.types import StringConstraints
from pydantic_settings import BaseSettings, SettingsConfigDict

NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class Settings(BaseSettings):
    DATABASE_URL: NonEmptyStr = Field(...)
    REDIS_URL: NonEmptyStr = Field(...)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
