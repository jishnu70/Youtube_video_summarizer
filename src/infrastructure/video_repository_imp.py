# src/infrastructure/video_repository_imp.py

from src.domain.entities import SummaryResponse, VideoResponse, VideoURL
from src.domain.video_repository import VideoRepository
from src.infrastructure.correction_service import Correction_Service
from src.infrastructure.database.mongo_service import MongoService
from src.infrastructure.stt_service import STTService
from src.infrastructure.summarizer_service import SummarizerService
from src.infrastructure.yt_service import YoutubeService
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class VideoRepositoryImp(VideoRepository):
    def __init__(self, db_url: str) -> None:
        self._db = MongoService(uri=db_url)
        self._yt_service = YoutubeService()
        self._stt_service = STTService(model_size="base")
        self._c_service = Correction_Service()
        self._s_service = SummarizerService()

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
        result = result[0]
        response = VideoResponse(
            _id = result["_id"],
            url = result["url"],
            transcription= result["transcript"],
            summaries = self._to_summary(result["summaries"]),
            created_at= result["created_at"]
        )
        return response

    async def _get_captions(self, url: str) -> Optional[str]:
        logger.debug("Fetching Captions")
        captions = self._yt_service.download_captions(url=url)
        return captions

    async def _get_transcription(self, url: str) -> str:
        logger.debug("Downloading audio...")
        chunks = await self._yt_service.download(url)
        logger.debug("Transcribing...")
        transcription = await self._stt_service.transcribe_audio(chunks)
        return transcription

    def _correct_grammer(self, transcription: str) -> str:
        logger.debug("\n--- Corrected Transcription ---\n")
        corrected_transcription = self._c_service.clean(transcription)
        return corrected_transcription

    def _generate_summary(self, c_transcription: str) -> str:
        logger.debug("\n--- Generate Summary ---\n")
        summary = self._s_service.summarize(c_transcription)
        return summary

    async def _transform_the_video(self, url: str) -> dict:
        captions = await self._get_captions(url)
        if captions is None or captions == "":
            transcription = await self._get_transcription(url)
            captions = self._correct_grammer(transcription)
        summary = self._generate_summary(captions)

        video_dict = {
            "url": url,
            "transcription": captions,
            "summary": summary
        }
        return video_dict

    async def get(self, video_url: Optional[VideoURL] = None, _id: Optional[str] = None)->VideoResponse:
        if video_url is None and _id is None:
            raise
        result = {}
        if video_url:
            result = await self._db.get_video(url=video_url.url)
            if result is None:
                result = await self._transform_the_video(url=video_url.url)
                db_id = await self.save(result)
                return await self.get(_id=db_id)
        elif _id:
            result = await self._db.get_video(_id=_id)
        if result is None or len(result.items()) == 0:
            raise
        return self._to_domain(result)

    async def save(self, summary: dict) -> str:
        result = await self._db.save(
            summary["url"],
            transcription=summary["transcription"],
            summary = summary["summary"],
        )
        return result
