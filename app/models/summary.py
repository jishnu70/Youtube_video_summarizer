# app/models/summary.py

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.task import Task
    from app.models.video import Video


class Summary(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, nullable=False)
    video_id: UUID = Field(
        ..., foreign_key="video.id", description="The ID of the associated video"
    )
    task_id: UUID = Field(
        ..., foreign_key="task.id", description="The ID of the associated task"
    )
    summary_text: str = Field(..., description="The generated summary text")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Creation timestamp",
        nullable=False,
    )

    # Relationships
    video: "Video" = Relationship(back_populates="summaries")
    task: "Task" = Relationship(back_populates="summary")
