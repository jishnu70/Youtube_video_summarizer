# src/presentation/container.py

from fastapi import Request
from src.application.use_case import UseCase

async def get_use_case(request: Request) -> UseCase:
    """Return the already initialized UseCase instance from app.state."""
    return request.app.state.use_case
