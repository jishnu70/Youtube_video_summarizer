# src/auth/tokens.py

from datetime import datetime, timedelta, timezone
from functools import lru_cache
from uuid import uuid4

import jwt
from fastapi import HTTPException
from src.auth.constants import (
    ACCESS_TOKEN_EXP,
    REFRESH_TOKEN_EXP,
    TOKEN_TYPE,
    CredentialsException,
    TokenData,
)


class TokenService:
    """
    Service for generating and verifying JWT tokens.
    This class provides methods to create access and refresh tokens,
    as well as to verify and refresh tokens.
    """

    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self._secret_key = secret_key
        self._algorithm = algorithm

    def _generate_token(self, user_id: str, exp: int, token_type: TOKEN_TYPE) -> str:
        now = datetime.now(timezone.utc)
        end_time = now + timedelta(seconds=exp)
        payload = {
            "jti": str(uuid4()),
            "sub": user_id,
            "token_type": token_type,
            "iat": int(now.timestamp()),
            "exp": int(end_time.timestamp()),
        }
        try:
            encoded_token = jwt.encode(
                payload, self._secret_key, algorithm=self._algorithm
            )
        except Exception as e:
            raise RuntimeError(f"Token generation failed: {str(e)}")
        return encoded_token

    def verify_token(self, token: str, expected_type: TOKEN_TYPE = "access") -> dict:
        try:
            payload = jwt.decode(token, self._secret_key, algorithms=[self._algorithm])
            user_id: str = payload.get("sub", "")
            if user_id == "":
                raise CredentialsException
            if payload.get("token_type") != expected_type:
                raise CredentialsException("Invalid token type")
        except jwt.ExpiredSignatureError:
            raise CredentialsException
        except jwt.InvalidTokenError:
            raise CredentialsException
        return payload

    def _create_access_token(self, user_id: str) -> str:
        return self._generate_token(user_id, exp=ACCESS_TOKEN_EXP, token_type="access")

    def _create_refresh_token(self, user_id: str) -> str:
        return self._generate_token(
            user_id, exp=REFRESH_TOKEN_EXP, token_type="refresh"
        )

    def new_access_token_from_refresh_token(self, token: str) -> TokenData:
        try:
            payload = self.verify_token(token, expected_type="refresh")
            user_id: str = payload.get("sub", "")
            if user_id == "":
                raise CredentialsException("Invalid token")
            return self.login(user_id)
        except HTTPException:
            raise
        except Exception as e:
            raise CredentialsException(f"Token refresh failed: {str(e)}")

    def login(self, user_id: str) -> TokenData:
        access_token = self._create_access_token(user_id)
        refresh_token = self._create_refresh_token(user_id)
        return TokenData(access_token=access_token, refresh_token=refresh_token)


@lru_cache()
def get_token_service(secret_key: str) -> TokenService:
    return TokenService(secret_key)
