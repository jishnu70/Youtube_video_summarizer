# src/auth/exceptions.py


from typing import Optional


class AuthException(Exception):
    """Base class for authentication-related exceptions."""

    pass


class FailedToFetchUserInfoException(AuthException):
    """Raised when fetching user info from the provider fails."""

    def __init__(self, provider: str, original_exception: Optional[Exception] = None):
        super().__init__(
            f"Failed to fetch user info from {provider}"
            + (f": {str(original_exception)}" if original_exception else "")
        )


class MissingProviderSubException(AuthException):
    """Raised when the 'sub' field is missing in the provider's user info."""

    def __init__(self, provider: str):
        super().__init__(f"Missing 'sub' field in {provider} user info.")


class UserNotFoundException(AuthException):
    """Raised when a user is not found in the database."""

    def __init__(self, user_id: str):
        super().__init__(f"User with ID {user_id} not found.")


class InvalidCredentialsException(AuthException):
    """Raised when provided credentials are invalid."""

    def __init__(self):
        super().__init__("Invalid username or password.")


class TokenExpiredException(AuthException):
    """Raised when a token has expired."""

    def __init__(self):
        super().__init__("Token has expired.")


class TokenInvalidException(AuthException):
    """Raised when a token is invalid."""

    def __init__(self):
        super().__init__("Token is invalid.")


class OAuthException(AuthException):
    """Raised when an OAuth-related error occurs."""

    def __init__(self, provider: str, message: str):
        super().__init__(f"OAuth error with {provider}: {message}")
