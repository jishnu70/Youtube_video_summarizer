# app/models/task.py

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Enum as SAEnum
from sqlmodel import Field, Relationship, SQLModel

from app.utils.constants import TaskStatus

if TYPE_CHECKING:
    from app.models.summary import Summary


class Task(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True, nullable=False)
    polling_id: str = Field(
        default_factory=lambda: uuid4().hex,
        unique=True,
        index=True,
        nullable=False,
        description="A unique identifier for polling the task status",
    )
    url: str = Field(
        ...,
        unique=True,
        index=True,
        nullable=False,
        description="The URL of the YouTube video associated with the task",
    )
    status: TaskStatus = Field(
        default=TaskStatus.PENDING,
        description="Status of the task (e.g., pending, in_progress, completed, failed)",
        nullable=False,
        sa_type=SAEnum(
            TaskStatus,
            values_callable=lambda enum_type: [status.value for status in enum_type],
        ),
    )
    err_message: str | None = Field(
        default=None,
        nullable=True,
        description="Error message if the task failed",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Creation timestamp",
        nullable=False,
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Last update timestamp",
        nullable=False,
    )

    summary: "Summary" = Relationship(
        back_populates="task", sa_relationship_kwargs={"uselist": False}
    )
