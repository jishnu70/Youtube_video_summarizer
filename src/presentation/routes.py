# src/presentation/routes.py

import logging
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, Response, status
from fastapi.responses import JSONResponse

from src.application.logging_config import setup_logging
from src.application.use_case import UseCase
from src.domain.entities import VideoResponse, VideoURL
from src.domain.model_exceptions import (
    FailedToFetch,
    FailedToSave,
    InsufficientData,
    TaskIDError,
    VideoNotAvailableError,
)
from src.infrastructure.mongo_service import MongoService
from src.infrastructure.redis_client import get_redis_client
from src.infrastructure.system_config import config
from src.infrastructure.video_repository_imp import VideoRepositoryImp
from src.presentation.container import get_use_case, requeue_stuck_tasks

setup_logging()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.warning("lifespan started")
    video_repo_impl = VideoRepositoryImp(config.DATABASE_URL)
    await video_repo_impl.connect_db()
    r_client = get_redis_client()
    m_client = MongoService(config.DATABASE_URL)
    await m_client.run_init()
    await requeue_stuck_tasks(m_client)
    repo_use_case = UseCase(video_repo_impl, r_client, m_client)
    app.state.use_case = repo_use_case
    logger.warning("lifespan set use_case")
    yield
    video_repo_impl.disconnect_db()
    await r_client.close()
    m_client.disconnect()
    logger.warning("lifespan ended")


app = FastAPI(
    title="Youtube Video Summarizer",
    version="1.1.2",
    description="API using FastAPI to get a summary of a youtube video",
    lifespan=lifespan,
)


@app.exception_handler(VideoNotAvailableError)
async def video_not_found_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND, content={"detail": str(exc)}
    )


@app.exception_handler(TaskIDError)
async def incorrect_task_id_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND, content={"detail": str(exc)}
    )


@app.exception_handler(InsufficientData)
async def insufficient_data_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST, content={"detail": str(exc)}
    )


@app.exception_handler(Exception)
async def generic_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"},
    )


@app.exception_handler(FailedToFetch)
async def fail_to_fetch_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"detail": str(exc)}
    )


@app.exception_handler(FailedToSave)
async def fail_to_save_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "There is a problem in the connection to the business logic"
        },
    )


@app.get("/")
def root():
    return Response("Backend is online")


@app.post("/", response_model=VideoResponse | str | dict)
async def get_summary(
    video: VideoURL, use_case: Annotated[UseCase, Depends(get_use_case)]
):
    return await use_case.send(video=video, task_id=None)


@app.post("/status")
async def get_status(task_id: str, use_case: Annotated[UseCase, Depends(get_use_case)]):
    return await use_case.send(task_id=task_id, video=None)
