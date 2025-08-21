# src/application/use_case.py

from src.application.dto import SummaryCompletedDTO, SummaryQueuedDTO, UrlDTO
from src.application.mappers import DTOMapper
from src.application.task_queue import TranscriptionTaskQueue
from src.domain.video_repository import VideoRepository

class UseCase:
    __video_repo: VideoRepository
    __video_queue: TranscriptionTaskQueue

    def __init__(self, video_repo: VideoRepository, video_queue: TranscriptionTaskQueue) -> None:
        self.__video_repo = video_repo
        self.__video_queue = video_queue

    async def _fetch_summary(self, url: str)->SummaryCompletedDTO|None:
        video = await self.__video_repo.get(DTOMapper.to_domain_url(url))
        if video and video.summary:
            return DTOMapper.to_summary_DTO(video)
        return None

    async def _generate_summary(self, url: str)->str:
        return await self.__video_queue.enqueue_video(url)

    async def send_url(self, url: UrlDTO)->SummaryCompletedDTO|SummaryQueuedDTO:
        summary = await self._fetch_summary(url.url)
        if summary is not None:
            return summary
        task_id = await self._generate_summary(url.url)
        return DTOMapper.to_queued_dto(url.url, task_id)
