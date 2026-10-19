# app/models/schemas.py
from pydantic import BaseModel, Field

from app.models.summary import Summary
from app.models.task import Task


class VideoSummaryRequest(BaseModel):
    url: str = Field(..., description="The URL of the YouTube video to summarize.")


class TaskStatusResponse(BaseModel):
    task: Task = Field(
        ..., description="The task object containing status information."
    )
    summary: Summary | None = Field(
        ..., description="The summary object if the task is completed."
    )

    class Config:
        from_attributes = True
