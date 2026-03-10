# src/domain/entities.py

from datetime import datetime
from typing import Optional

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


class TaskStatusResponse(BaseModel):
    task_id: str = Field(..., description="Unique identifier for the task")
    status: Optional[str] = Field(
        default=None,
        description="Status of the task. Can be 'queued', 'processing', 'completed', 'failed', or None if not found.",
    )
    message: Optional[str] = Field(
        default=None,
        description="Additional information about the task status, such as error messages if the task failed.",
    )
