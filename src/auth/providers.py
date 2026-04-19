# src/auth/providers.py


import logging
from functools import lru_cache

from fastapi import Request

from src.auth.base import OAuthBase, oauth
from src.auth.constants import TokenData
from src.auth.exceptions import (
    FailedToFetchUserInfoException,
    MissingProviderSubException,
    OAuthException,
)
from src.models.user import ProviderInfo, UserDB

logger = logging.getLogger(__name__)


class GoogleAuth(OAuthBase):
    def __init__(
        self,
        secret_key: str,
        google_client_id: str,
        google_client_secret: str,
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

    async def handle_callback(self, request: Request) -> TokenData:
        try:
            token = await oauth.google.authorize_access_token(request)
            user_info = token.get("userinfo", {})
            if not user_info:
                raise FailedToFetchUserInfoException("Google")
            provider_user_id = user_info.get("sub", None)
            if not provider_user_id:
                raise MissingProviderSubException("Google")
            user_email = user_info.get("email", None)
            if not user_email:
                raise FailedToFetchUserInfoException("Google")
            user_obj = UserDB(
                provider=ProviderInfo(
                    name="google",
                    user_id=provider_user_id,
                ),
                email=user_email,
                username=user_email.split("@")[0],  # use name before @ default username
            )
            user = await self.user_repo.find_or_create_user(user_obj)
            self_tokens = self.token_service.login(str(user.id))
            return self_tokens
        except (FailedToFetchUserInfoException, MissingProviderSubException):
            raise
        except Exception as e:
            logger.error(f"Error handling Google OAuth callback: {str(e)}")
            raise OAuthException(
                "Google", f"Google OAuth callback handling failed: {str(e)}"
            )


@lru_cache()
def get_google_auth(
    secret_key: str,
    google_client_id: str,
    google_client_secret: str,
) -> GoogleAuth:
    return GoogleAuth(secret_key, google_client_id, google_client_secret)
