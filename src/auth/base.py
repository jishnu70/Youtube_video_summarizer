# src/auth/base.py

from typing import Optional

from authlib.integrations.starlette_client import OAuth
from fastapi import Request
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, model_validator

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


class OAuthBase(AuthBase):
    def __init__(self, secret_key: str):
        super().__init__(secret_key)

    async def initiate_oauth(self, request: Request, redirect_url: str) -> None: ...
    async def handle_callback(self, request: Request) -> dict: ...


class GoogleAuth(OAuthBase):
    def __init__(
        self, secret_key: str, google_client_id: str, google_client_secret: str
    ):
        super().__init__(secret_key)
        self.g_c_i = google_client_id
        self.g_c_s = google_client_secret

    async def initiate_oauth(
        self,
        request: Request,
        redirect_url: str,
    ) -> None:
        return await oauth.google.authorize_redirect(request, redirect_url)

    async def handle_callback(self, request: Request) -> dict:
        token = await oauth.google.authorize_access_token(request)
        user_info = await oauth.google.parse_id_token(request, token)
        return user_info

    def verify_google_token(self, token: str) -> bool:
        ...
        # Implement Google token verification logic here
