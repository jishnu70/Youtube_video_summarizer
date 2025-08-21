# src/domain/model_exceptions.py

class UniqueIDError(Exception):
    """Error in the primary key"""
    pass

class IncompleteError(Exception):
    """If the summary was not generated"""
    pass
