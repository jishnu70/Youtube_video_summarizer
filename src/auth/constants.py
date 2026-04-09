# src/auth/constants.py

from typing import Literal, Optional

from fastapi import HTTPException, status
from pydantic import BaseModel

ACCESS_TOKEN_EXP = 15 * 60  # 15 minutes
REFRESH_TOKEN_EXP = 7 * 24 * 60 * 60  # 7 days
TOKEN_TYPE = Literal["access", "refresh"]


class TokenData(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"


class CredentialsException(HTTPException):
    def __init__(self, detail: str = "Could not validate credentials"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )
