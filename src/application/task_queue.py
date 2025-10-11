# src/application/task_queue.py

from abc import ABC, abstractmethod

class TranscriptionTaskQueue(ABC):
    @abstractmethod
    async def enqueue_video(self, url: str)->str:
        """Add video URL to the queue and return task ID"""
        pass

    @abstractmethod
    async def save_task_metadata(self, task_id: str, url: str, status: str) -> None:
        """Save task metadata to MongoDB"""
        pass
