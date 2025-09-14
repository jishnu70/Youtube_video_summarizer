# src/domain/entities.py

from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class VideoURL(BaseModel):
    _id: Optional[str]
    url: str

class SummaryResponse(BaseModel):
    summary: str
    model_name: str
    latest: bool
    created_at: datetime

class VideoResponse(VideoURL):
    transcription: str
    summaries: SummaryResponse
    created_at: datetime
