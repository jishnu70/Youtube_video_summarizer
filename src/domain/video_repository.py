# src/domain/video_repository.py

from abc import ABC, abstractmethod
from domain.entities import VideoResponse, VideoURL

class VideoRepository(ABC):
    @abstractmethod
    async def get(self, video_url:VideoURL)->VideoResponse|None:
        """Check if the summary is present in the db"""
        pass

    @abstractmethod
    async def save(self, summary: VideoResponse)->None:
        """Save the summary in the db"""
        pass
