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
