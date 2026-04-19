# src/auth/base.py

from typing import Optional

from authlib.integrations.starlette_client import OAuth
from fastapi import Request
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, model_validator
from src.repo.user_repo import get_user_repo

from src.auth.constants import TokenData
from src.auth.tokens import get_token_service

oauth = OAuth()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


class OAuthProvider(BaseModel):
    name: str
    client_id: str
    client_secret: str
    server_metadata_url: Optional[str] = None
    client_kwargs: Optional[dict] = None

    @model_validator(mode="before")
    @classmethod
    def validate_content(cls, values):
        field_names = ["name", "client_id", "client_secret"]

        def check_empty_field(field_name: str) -> None:
            value = values.get(field_name, "")
            if value.strip() == "":
                raise ValueError(f"{field_name.replace('_', ' ').title()} is required")

        for field_name in field_names:
            check_empty_field(field_name)
        return values


def register_oauth(providers: list[OAuthProvider]) -> None:
    """To be called one time in app lifespan to register OAuth providers."""
    for provider in providers:
        oauth.register(
            name=provider.name,
            client_id=provider.client_id,
            client_secret=provider.client_secret,
            server_metadata_url=provider.server_metadata_url,
            client_kwargs=provider.client_kwargs,
        )


class AuthBase:
    def __init__(self, secret_key: str):
        self.secret_key = secret_key
        self.token_service = get_token_service(secret_key)
        self.user_repo = get_user_repo()


class OAuthBase(AuthBase):
    def __init__(self, secret_key: str):
        super().__init__(secret_key)

    async def initiate_oauth(self, request: Request, redirect_url: str) -> None: ...
    async def handle_callback(self, request: Request) -> TokenData: ...
