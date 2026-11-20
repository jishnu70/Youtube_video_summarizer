# app/utils/constants.py

from enum import Enum, IntEnum


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class RateLimitConstants(IntEnum):
    MAX_REQUESTS = 5
    WINDOW_SIZE = 60  # in seconds
