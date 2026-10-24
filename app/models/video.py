# app/models/video.py

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.summary import Summary


class Video(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, nullable=False)
    url: str = Field(
        ...,
        unique=True,
        index=True,
        nullable=False,
        description="The URL of the YouTube video",
    )
    title: str | None = Field(
        default=None, nullable=True, description="Title of the video"
    )
    duration: int | None = Field(
        default=None, nullable=True, description="Duration of the video in seconds"
    )
    transcript: str = Field(..., description="Transcript of the video", nullable=False)
    has_native_captions: bool = Field(
        default=False, description="Indicates if the video has native captions"
    )
    stt_model_used: str | None = Field(
        default=None,
        nullable=True,
        description="The speech-to-text model used for transcription",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Creation timestamp",
        nullable=False,
    )

    summaries: list["Summary"] = Relationship(back_populates="video")
