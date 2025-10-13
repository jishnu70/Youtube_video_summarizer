# src/infrastructure/video_repository_imp.py

from src.domain.entities import SummaryResponse, VideoResponse, VideoURL
from src.domain.model_exceptions import FailedToFetch, FailedToSave, InsufficientData, VideoNotAvailableError
from src.domain.video_repository import VideoRepository
from src.infrastructure.mongo_service import MongoService
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class VideoRepositoryImp(VideoRepository):
    def __init__(self, db_url: str) -> None:
        self._db = MongoService(uri=db_url)

    async def connect_db(self):
        return await self._db.connect()

    def __init_subclass__(cls) -> None:
        return super().__init_subclass__()

    def _to_summary(self, summaries: dict) -> SummaryResponse:
        return SummaryResponse(
            summary= summaries["summary"],
            model_name= summaries["model_name"],
            latest = summaries["latest"],
            created_at= summaries["created_at"]
        )

    def _to_domain(self, result: dict) -> VideoResponse:
        # result = result[0]
        response = VideoResponse(
            _id = result["_id"],
            url = result["url"],
            transcription= result["transcription"],
            summaries = self._to_summary(result["summaries"][0]),
            created_at= result["created_at"]
        )
        return response

    async def get(self, video_url: Optional[VideoURL] = None, _id: Optional[str] = None)->Optional[VideoResponse]:
        try:
            if video_url:
                result = await self._db.get_video(url=video_url.url)
                if result is None:
                    logger.warning(f"Video {video_url.url} not found")
                    return None
            elif _id:
                result = await self._db.get_video(_id=_id)
                if result is None:
                    raise VideoNotAvailableError(f"Video with id {_id} not found")
            else:
                raise InsufficientData("Either video_url or _id must be provided")

            return self._to_domain(result)
        except Exception as e:
            logger.error(f"Repository get failed: {str(e)}")
            raise FailedToFetch("Failed to fetch the video")

    async def save(self, summary: VideoResponse) -> VideoResponse:
        try:
            result = await self._db.save(
                summary.url,
                transcription=summary.transcription,
                summary = summary.summaries.summary,
                model_name=summary.summaries.model_name
            )
            logger.info(f"Saved video summary for {summary.url} with id {result}")
            summary._id=result
            return summary
        except Exception as e:
            logger.error(f"Repository save failed: {str(e)}")
            raise FailedToSave("Failed to save the video and summary")
