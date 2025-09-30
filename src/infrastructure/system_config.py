# src/infrastructure/system_config.py

from pydantic_settings import BaseSettings, SettingsConfigDict

class Config(BaseSettings):
    DATABASE_URL: str = ""
    REDIS_URL: str = ""
    CELERY_BROKER_URL: str = ""
    CELERY_BACKEND_URL: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

config = Config()
