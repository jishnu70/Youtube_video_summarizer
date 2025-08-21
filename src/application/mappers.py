# src/application/mappers.py

from typing import Optional
from src.domain.entities import VideoResponse, VideoURL
from src.domain.model_exceptions import IncompleteError, UniqueIDError
from src.application.dto import SummaryCompletedDTO, SummaryQueuedDTO

class DTOMapper:
    @staticmethod
    def to_domain_url(url:str, id:Optional[str] = None)->VideoURL:
        return VideoURL(id=id, url=url)

    @staticmethod
    def to_summary_DTO(summary: VideoResponse)->SummaryCompletedDTO:
        if summary.id is None:
            raise UniqueIDError("Transcription is missing a primary key")
        if summary.summary is None:
            raise IncompleteError("Failed to generate summary")
        return SummaryCompletedDTO(
            id=summary.id,
            url=summary.url,
            summary=summary.summary
        )

    @staticmethod
    def to_queued_dto(url: str, task_id: str)->SummaryQueuedDTO:
        return SummaryQueuedDTO(
            id=None,
            url=url,
            task_id=task_id,
            task_message="Processing the video"
        )
