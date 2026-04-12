# src/models/user.py

from datetime import datetime, timezone
from typing import Annotated, Any, Optional

from pydantic import BaseModel, BeforeValidator, Field, model_validator

STR_ID = Annotated[str, BeforeValidator(lambda v: str(v) if v is not None else None)]


class ProviderInfo(BaseModel):
    name: str = Field(..., description="OAuth provider name")
    user_id: str = Field(..., description="User ID from the OAuth provider")


class UserBase(BaseModel):
    id: Optional[STR_ID] = Field(
        default=None, alias="_id", description="Unique identifier for the user"
    )
    username: str = Field(..., description="Username of the user")
    email: str = Field(..., description="Email address of the user")
    provider: Optional[ProviderInfo] = Field(
        default=None, description="OAuth provider used for authentication"
    )
    created_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp when the user was created",
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        description="Timestamp when the user was last updated",
    )


class UserDB(UserBase):
    hashed_password: Optional[str] = Field(
        default=None,
        description="Hashed password for local authentication",
    )

    @classmethod
    def from_db(cls, data: dict[str, Any]) -> "UserDB":
        return cls(**data)

    @property
    def now(self) -> datetime:
        return datetime.now(timezone.utc)

    @model_validator(mode="before")
    @classmethod
    def validate_provider_and_password(cls, values: dict[str, Any]) -> dict[str, Any]:
        provider = values.get("provider")
        hashed_password = values.get("hashed_password")
        if provider and hashed_password:
            raise ValueError("User cannot have both provider info and hashed password")
        if not provider and not hashed_password:
            raise ValueError("User must have either provider info or hashed password")
        return values

    @model_validator(mode="after")
    def validate_timestamps(self) -> "UserDB":
        if not self.created_at:
            self.created_at = self.now
        if not self.updated_at:
            self.updated_at = self.now
        return self

    def to_dict(self, *args, **kwargs) -> dict[str, Any]:
        data = super().model_dump(*args, **kwargs)
        if self.provider and self.hashed_password:
            raise ValueError("User cannot have both provider info and hashed password")
        if not self.provider and not self.hashed_password:
            raise ValueError("User must have either provider info or hashed password")
        return data


class UserResponse(UserBase): ...
