# src/application/video_pipeline_service.py

from typing import Optional
import logging
from src.domain.entities import SummaryResponse, VideoResponse
from src.infrastructure.correction_service import Correction_Service
from src.infrastructure.stt_service import STTService
from src.infrastructure.summarizer_service import SummarizerService
from src.infrastructure.yt_service import YoutubeService

logger = logging.getLogger(__name__)

class VideoPipelineService:
    def __init__(self,
        yt_service: YoutubeService,
        stt_service: STTService,
        c_service: Correction_Service,
        s_service: SummarizerService
    ) -> None:
        self._yt_service = yt_service
        self._stt_service = stt_service
        self._c_service = c_service
        self._s_service = s_service

    def _get_captions(self, url: str) -> Optional[str]:
        logger.debug("Fetching Captions")
        captions = self._yt_service.download_captions(url=url)
        return captions

    async def _get_transcription(self, url: str) -> str:
        logger.debug(f"Downloading audio: {url}")
        chunks = await self._yt_service.download(url)
        logger.debug(f"Transcribing: {url}")
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

    async def transform_the_video(self, url: str) -> VideoResponse:
        captions = self._get_captions(url)
        if captions is None or captions == "":
            transcription = await self._get_transcription(url)
            captions = self._correct_grammer(transcription)
        if not captions:
            raise ValueError(f"Could not get captions or transcription for {url}")

        summary = self._generate_summary(captions)

        video_response = VideoResponse(
            _id=None,
            url=url,
            transcription=captions,
            summaries=SummaryResponse(
                summary=summary,
                model_name="google/flan-t5-large",
                latest=True,
                created_at=None
            ),
            created_at=None  # DB will populate this
        )
        return video_response
