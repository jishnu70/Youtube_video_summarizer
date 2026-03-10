# src/application/use_case.py

import logging
from typing import Optional

import redis

from src.background.celery_app import celery_app
from src.domain.entities import TaskStatusResponse, VideoResponse, VideoURL
from src.domain.model_exceptions import InsufficientData, TaskIDError
from src.domain.video_repository import VideoRepository
from src.infrastructure.mongo_service import MongoService
from src.infrastructure.redis_client import RedisClient

logger = logging.getLogger(__name__)


class UseCase:
    _video_rep: VideoRepository
    _redis_client: RedisClient
    _mongo_client: MongoService

    def __init__(
        self, vid_repo: VideoRepository, r_client: RedisClient, m_client: MongoService
    ) -> None:
        self._video_rep = vid_repo
        self._redis_client = r_client
        self._mongo_client = m_client

    async def _get_from_redis(self, video: VideoURL) -> Optional[VideoResponse]:
        """check if the video is already cached in redis"""
        logger.warning("fetching from redis")
        response = await self._redis_client.get_cached_summary(url=video.url)
        if response is not None:
            logger.info("Cache hit")
        else:
            logger.info("Cache miss")
        return response

    async def _get_from_db(self, video: VideoURL) -> Optional[VideoResponse]:
        """check if the video is already saved in db"""
        logger.info("fetching from database")
        response = await self._video_rep.get(video_url=video, _id=None)
        if response:
            logger.info("Database hit")
            logger.info(f"caching the summary of: {response.url}")
            await self._redis_client.set_cache_summary(response)
        else:
            logger.info("Database miss")
        return response

    async def _check_if_queued(
        self, task_id: Optional[str], video: Optional[VideoURL]
    ) -> Optional[dict]:
        """check if the video is already queued for Celery"""
        if task_id:
            return await self._mongo_client.get_status(task_id=task_id, video_url=None)
        elif video:
            return await self._mongo_client.get_status(
                task_id=task_id, video_url=video.url
            )
        else:
            raise InsufficientData("The request is missing the required informations")

    async def _combine_redis_db(self, video: VideoURL) -> Optional[VideoResponse]:
        vid_response: Optional[VideoResponse] = None
        vid_response = await self._get_from_redis(video)
        if vid_response is None:
            vid_response = await self._get_from_db(video)
        return vid_response

    async def send(
        self, video: Optional[VideoURL] = None, task_id: Optional[str] = None
    ) -> VideoResponse | TaskStatusResponse:
        try:
            is_queued = await self._check_if_queued(task_id=task_id, video=video)
            if is_queued:
                queued_status = is_queued.get("status", None)
                queued_task_id = is_queued.get("task_id", None)
                if not queued_status or not queued_task_id:
                    logger.warning(
                        f"Task status record for task_id {task_id} is missing 'status' or 'task_id' fields"
                    )
                    raise RuntimeError(
                        f"Invalid task status record for task_id {task_id}"
                    )
                if queued_status in ("QUEUED", "STARTED"):
                    return TaskStatusResponse(
                        task_id=queued_task_id,
                        status=queued_status,
                        message="Video already queued for processing",
                    )
                elif queued_status in ["TIMEOUT", "FAILED"]:
                    raise RuntimeError(
                        f"Previous task {queued_task_id} failed or timed out: {queued_status}"
                    )
                elif queued_status == "SUCCESS":
                    video = VideoURL(_id=None, url=is_queued["video_url"])
            if video:
                redis_task = await self._redis_client.get_queued_task(url=video.url)
                if redis_task:
                    return TaskStatusResponse(
                        task_id=redis_task,
                        message="Video already queued for processing",
                    )
                response = await self._combine_redis_db(video)
                if response is None:
                    from uuid import uuid4

                    new_task_id = str(uuid4())

                    claimed_task = await self._redis_client.set_queued_task(
                        taskID=new_task_id, url=video.url
                    )
                    if not claimed_task:
                        old_task_id = await self._redis_client.get_queued_task(
                            url=video.url
                        )
                        if old_task_id is None:
                            logger.warning(
                                f"Failed to claim queue for {video.url} and no existing task found in Redis"
                            )
                            raise RuntimeError(
                                f"Failed to claim queue for {video.url} and no existing task found in Redis"
                            )
                        logger.info(
                            f"Another task already queued for {video.url} with taskID {claimed_task}"
                        )
                        return TaskStatusResponse(
                            task_id=old_task_id,
                            message="Video already queued for processing",
                        )

                    await self._mongo_client.insert_task_status(new_task_id, video.url)

                    try:
                        task = celery_app.send_task(
                            "summarize_video_task",
                            args=[video.url],
                            task_id=new_task_id,
                        )
                    except Exception as e:
                        logger.exception(f"Failed to send Celery task: {e}")
                        await self._redis_client.delete_queued_task(video.url)
                        raise Exception("Failed to start the distributed task") from e
                    return TaskStatusResponse(
                        task_id=task.id,
                        message="Video is being processed",
                    )
                return response

            raise TaskIDError("Incorrect data, please provide a valid ID")
        except redis.RedisError as re:
            logger.error(f"Redis error: {re}")
            raise Exception("Cache error")
        except Exception as e:
            logger.error(f"UseCase send failed: {e}")
            raise
