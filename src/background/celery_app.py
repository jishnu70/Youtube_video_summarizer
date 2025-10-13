# src/background/celery_app.py

from celery import Celery
from src.infrastructure.system_config import config


print("CELERY BROKER URL:", config.CELERY_BROKER_URL)  # debug
print("CELERY BACKEND URL:", config.CELERY_BACKEND_URL)  # debug

celery_app = Celery(
    "yt-service",
    broker=config.CELERY_BROKER_URL,
    backend=config.CELERY_BACKEND_URL,
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

from src.background import celery_task
