# app/config.py

from functools import lru_cache
from typing import Annotated

from pydantic import Field, field_validator
from pydantic.types import StringConstraints
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class Settings(BaseSettings):
    DATABASE_URL: NonEmptyStr = Field(...)
    REDIS_URL: NonEmptyStr = Field(...)
    SQL_ECHO: bool = False
    ALLOWED_ORIGINS: Annotated[list[str], NoDecode] = ["*"]

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        return value.replace("sslmode=require", "ssl=require")

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_allowed_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, list):
            return value
        origins = [origin.strip() for origin in value.split(",") if origin.strip()]
        return origins or ["*"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
