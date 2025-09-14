# src/application/dto.py

from typing import Optional
from pydantic import BaseModel, Field

class UrlDTO(BaseModel):
    _id: Optional[str]
    url: str = Field(..., pattern=r"^https:\/\/(www\.)?(youtube\.com|youtu\.be)\/")

class TranscriptionDTO(UrlDTO):
    transcript: str

class SummaryQueuedDTO(UrlDTO):
    task_id: str
    task_message: str

class SummaryCompletedDTO(UrlDTO):
    summary: str
