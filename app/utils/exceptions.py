# app/utils/exceptions.py


class DataNotFound(Exception):
    """Exception raised when a requested resource is not found."""

    def __init__(self, message: str = "Resource not found"):
        self.message = message
        super().__init__(self.message)


class DataNotCreated(Exception):
    """Exception raised when a requested resource is not created."""

    def __init__(self, message: str = "Resource not created"):
        self.message = message
        super().__init__(self.message)
