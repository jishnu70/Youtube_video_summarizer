# src/domain/video_repository.py

from abc import ABC, abstractmethod
from domain.entities import VideoResponse, VideoURL
from typing import Optional

class VideoRepository(ABC):
    @abstractmethod
    async def get(self, video_url: Optional[VideoURL], _id: Optional[str]) -> VideoResponse:
        """Check if the summary is present in the db"""
        pass

    @abstractmethod
    async def save(self, summary: VideoResponse) -> VideoResponse:
        """Save the summary in the db"""
        pass
