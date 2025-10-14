# src/application/use_case.py

from typing import Optional
import redis
from src.background.celery_task import queue_yt_video
from src.domain.entities import VideoResponse, VideoURL
from src.domain.model_exceptions import InsufficientData, TaskIDError
from src.domain.video_repository import VideoRepository
from src.infrastructure.mongo_service import MongoService
from src.infrastructure.redis_client import RedisClient
import logging

logger = logging.getLogger(__name__)

class UseCase:
    _video_rep: VideoRepository
    _redis_client: RedisClient
    _mongo_client: MongoService

    def __init__(self, vid_repo: VideoRepository, r_client: RedisClient, m_client: MongoService) -> None:
        self._video_rep = vid_repo
        self._redis_client = r_client
        self._mongo_client = m_client

    async def _get_from_redis(self, video: VideoURL) -> Optional[VideoResponse]:
        """check if the video is already cached in redis"""
        logger.warning("fetching from redis")
        return await self._redis_client.get_cached_summary(url=video.url)

    async def _get_from_db(self, video: VideoURL) -> Optional[VideoResponse]:
        """check if the video is already saved in db"""
        logger.warning("fetching from database")
        response = await self._video_rep.get(video_url=video, _id=None)
        if response:
            await self._redis_client.set_cache_summary(response)
        return response

    async def _check_if_queued(self, requestID: Optional[str], video: Optional[VideoURL]) -> Optional[dict]:
        """check if the video is already queued for Celery"""
        if requestID:
            return await self._mongo_client.get_status(requestID=requestID, video_url=None)
        elif video:
            return await self._mongo_client.get_status(requestID=requestID, video_url=video.url)
        else:
            raise InsufficientData("The request is missing the required informations")

    async def _combine_redis_db(self, video: VideoURL) -> Optional[VideoResponse]:
        vid_response: Optional[VideoResponse]
        vid_response = await self._get_from_redis(video)
        if vid_response is None:
            vid_response = await self._get_from_db(video)
        return vid_response

    async def send(self, video: Optional[VideoURL] = None, task_id: Optional[str] = None) -> VideoResponse | str | dict:
        try:
            is_queued = await self._check_if_queued(requestID=task_id, video=video)
            if is_queued:
                status = is_queued["status"]
                if status in ["QUEUED", "STARTED"]:
                    return {
                        "task_id": is_queued["task_id"],
                        "status": status,
                        "message": "Video already queued for processing"
                    }
                elif status in ["TIMEOUT", "FAILED"]:
                    raise RuntimeError(f"Previous task {is_queued['task_id']} failed or timed out: {status}")
                elif status == "SUCCESS":
                    video = VideoURL(_id=None,url=is_queued["video_url"])
            if video:
                redis_task = await self._redis_client.get_queued_task(url=video.url)
                if redis_task:
                    return {
                        "task_id": redis_task,
                        "message": "Video already queued for processing"
                    }
                response = await self._combine_redis_db(video)
                if response is None:
                    task = queue_yt_video.delay(video.url)
                    new_task_id = task.id
                    await self._redis_client.set_queued_task(taskID=new_task_id, url=video.url)
                    await self._mongo_client.insert_task_status(new_task_id, video.url)
                    return new_task_id
                return response

            raise TaskIDError("Incorrect data, please provide a valid ID")
        except redis.RedisError as re:
            logger.error(f"Redis error: {re}")
            raise Exception("Cache error")
        except Exception as e:
            logger.error(f"UseCase send failed: {e}")
            raise
