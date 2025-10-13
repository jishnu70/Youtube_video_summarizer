# src/domain/model_exceptions.py

class UniqueIDError(Exception):
    """Error in the primary key"""
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
