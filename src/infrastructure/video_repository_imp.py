# src/infrastructure/video_repository_imp.py

from src.domain.entities import SummaryResponse, VideoResponse, VideoURL
from src.domain.model_exceptions import InsufficientData
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
        prompt = f"""
            Summarize the following transcription exactly as it is.

            Rules:
            1. Only use sentences or phrases that appear in the transcription.
            2. Do NOT include any social media mentions, emails, calls-to-action, or invented content.
            3. Do NOT mention YouTube, Twitter, Facebook, blogs, or any external platform.
            4. Keep the summary factual, concise, and limited to the content.
            5. Ignore any phrases like 'hit subscribe', 'share this video', or 'contact me'.

            Output only the summary. No extra commentary.

            Transcription:
            {c_transcription}
        """
        summary = self._s_service.summarize(prompt)
        return summary

    async def _transform_the_video(self, url: str) -> VideoResponse:
        captions = await self._get_captions(url)
        if captions is None or captions == "":
            transcription = await self._get_transcription(url)
            captions = self._correct_grammer(transcription)
        summary = self._generate_summary(captions)

        video_response = VideoResponse(
            _id=None,  # not yet stored in DB
            url=url,
            transcription=captions,
            summaries=SummaryResponse(
                summary=summary,
                model_name="summarizer-service",   # you can replace with actual model name if available
                latest=True,
                created_at=None   # can be set to datetime.utcnow() if you want
            ),
            created_at=None  # DB will populate this
        )
        return video_response

    async def get(self, video_url: Optional[VideoURL] = None, _id: Optional[str] = None)->VideoResponse:
        if video_url is None and _id is None:
            raise InsufficientData("Either video_url or _id must be provided")

        if video_url:
            result = await self._db.get_video(url=video_url.url)
            if result is None:
                result = await self._transform_the_video(url=video_url.url)
                saved_data = await self.save(result)
                return saved_data
        elif _id:
            result = await self._db.get_video(_id=_id)
            if result is None or len(result.items()) == 0:
                raise ValueError(f"Video with id {_id} not found")
        return self._to_domain(result)

    async def save(self, summary: VideoResponse) -> VideoResponse:
        result = await self._db.save(
            summary.url,
            transcription=summary.transcription,
            summary = summary.summaries.summary,
            model_name=summary.summaries.model_name
        )
        print(f"Result = {result}")
        summary._id=result
        return summary
