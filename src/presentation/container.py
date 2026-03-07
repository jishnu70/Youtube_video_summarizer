# src/presentation/container.py

import logging

from fastapi import Request

from src.application.task_maintenance import TaskMaintenanceService
from src.application.use_case import UseCase
from src.infrastructure.mongo_service import MongoService

logger = logging.getLogger(__name__)


async def get_use_case(request: Request) -> UseCase:
    """Return the already initialized UseCase instance from app.state."""
    return request.app.state.use_case


async def requeue_stuck_tasks(request: Request) -> dict[str, str]:
    """
    FastAPI endpoint or startup task that triggers maintenance service.
    The request handler should only orchestrate, not contain requeue logic.
    """
    mongo: MongoService = request.app.state.mongo
    maintainance_service = TaskMaintenanceService(mongo)
    await maintainance_service.requeue_stuck_tasks()
    return {"status": "requeue attempted"}
