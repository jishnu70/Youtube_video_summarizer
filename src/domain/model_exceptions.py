# src/domain/model_exceptions.py


class DatabaseUnavailableError(Exception):
    """Raised when the database is unavailable or connection fails."""

    def __init__(
        self,
        message: str = "Database is currently unavailable. Please try again later.",
    ):
        self.message = message
        super().__init__(self.message)


class UniqueIDError(Exception):
    """Error in the primary key"""

    pass


class TaskIDError(Exception):
    """Provided incorrect task ID"""

    pass


class IncompleteError(Exception):
    """If the summary was not generated"""

    pass


class VideoNotAvailableError(Exception):
    """If the URL or video does not exists"""

    pass


class InsufficientData(Exception):
    """Insufficient data is given"""

    pass


class SummaryFailException(Exception):
    """Summary generation for the video fails"""

    pass


class FailedToFetch(Exception):
    """Failed to fetch the data in db or cache"""

    pass


class FailedToSave(Exception):
    """Failed to save the data in db or cache"""

    pass


class SoftTimeLimitExceededError(Exception):
    """Soft Time Limit Exceeded"""

    pass


class RecordNotFoundError(Exception):
    """Record not found in the database"""

    def __init__(self, message: str = "Record not found in the database"):
        self.message = message
        super().__init__(self.message)
