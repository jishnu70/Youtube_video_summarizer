# src/domain/entities.py

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

class VideoURL(BaseModel):
    _id: Optional[str]
    url: str = Field(..., pattern=r"^https:\/\/(www\.)?(youtube\.com|youtu\.be)\/")

class SummaryResponse(BaseModel):
    summary: str
    model_name: str
    latest: bool
    created_at: Optional[datetime]

class VideoResponse(VideoURL):
    transcription: str
    summaries: SummaryResponse
    created_at: Optional[datetime]
