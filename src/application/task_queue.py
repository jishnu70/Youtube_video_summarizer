# src/application/task_queue.py

from abc import ABC, abstractmethod

class TranscriptionTaskQueue(ABC):
    @abstractmethod
    async def enqueue_video(self, url: str)->str:
        """Add video url to the queue"""
        pass
