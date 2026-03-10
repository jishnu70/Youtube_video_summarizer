# src/infrastructure/video_repository_imp.py

import logging
from typing import Optional

from bson.errors import InvalidId
from pymongo.errors import PyMongoError

from src.domain.entities import SummaryResponse, VideoResponse, VideoURL
from src.domain.model_exceptions import (
    FailedToFetch,
    FailedToSave,
    InsufficientData,
    VideoNotAvailableError,
)
from src.domain.video_repository import VideoRepository
from src.infrastructure.mongo_service import MongoService

logger = logging.getLogger(__name__)


class VideoRepositoryImp(VideoRepository):
    def __init__(self, mongo_service: MongoService) -> None:
        self._db = mongo_service

    def _to_summary(self, summaries: dict) -> SummaryResponse:
        return SummaryResponse(
            summary=summaries["summary"],
            model_name=summaries["model_name"],
            latest=summaries["latest"],
            created_at=summaries["created_at"],
        )

    def _to_domain(self, result: dict) -> VideoResponse:
        # result = result[0]
        response = VideoResponse(
            _id=result["_id"],
            url=result["url"],
            transcription=result["transcription"],
            summaries=self._to_summary(result["summaries"][0]),
            created_at=result["created_at"],
        )
        return response

    async def get(
        self, video_url: Optional[VideoURL] = None, _id: Optional[str] = None
    ) -> Optional[VideoResponse]:
        if video_url is None and _id is None:
            raise InsufficientData("Either video_url or _id must be provided")
        try:
            result = await self._db.get_video(
                url=video_url.url if video_url else None, _id=_id
            )
            if result is None:
                if video_url:
                    logger.info(f"Video not found for URL: {video_url.url}")
                    return None
                # if _id is provided but not found, it's an error
                logger.info(f"Video not found for ID: {_id}")
                raise VideoNotAvailableError("The requested video is not available")

            return self._to_domain(result)
        except (VideoNotAvailableError, InsufficientData):
            raise
        except InvalidId as e:
            logger.error(f"Invalid ID format: {str(e)}")
            raise VideoNotAvailableError("The requested video is not available") from e
        except PyMongoError as e:
            logger.error(f"MongoDB error while fetching video: {str(e)}")
        except Exception as e:
            logger.error(f"Repository get failed: {str(e)}")
            raise FailedToFetch("Failed to fetch the video")

    async def save(self, summary: VideoResponse) -> VideoResponse:
        try:
            result = await self._db.save(
                summary.url,
                transcription=summary.transcription,
                summary=summary.summaries.summary,
                model_name=summary.summaries.model_name,
            )
            if result is None:
                logger.error("Repository save failed: No result returned from database")
                raise FailedToSave("Failed to save the video and summary")
            logger.info(f"Saved video summary for {summary.url} with id {result}")
            summary._id = result["_id"]
            summary.created_at = result["created_at"]
            summary.summaries.created_at = (
                result["summaries"][0]["created_at"]
                if result.get("summaries") is not None
                else None
            )
            return summary
        except Exception as e:
            logger.error(f"Repository save failed: {str(e)}")
            raise FailedToSave("Failed to save the video and summary")
