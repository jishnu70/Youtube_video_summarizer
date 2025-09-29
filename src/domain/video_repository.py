# src/domain/video_repository.py

from abc import ABC, abstractmethod
from src.domain.entities import VideoResponse, VideoURL
from typing import Optional

class VideoRepository(ABC):
    @abstractmethod
    async def get(self, video_url: Optional[VideoURL], _id: Optional[str]) -> Optional[VideoResponse]:
        """Check if the summary is present in the db"""
        pass

    @abstractmethod
    async def save(self, summary: VideoResponse) -> VideoResponse:
        """Save the summary to the db"""
        pass
