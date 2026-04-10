# src/models/user.py

from datetime import datetime
from typing import Annotated, Optional

from pydantic import BaseModel, BeforeValidator, Field

STR_ID = Annotated[str, BeforeValidator(lambda v: str(v) if v is not None else None)]


class UserBase(BaseModel):
    id: Optional[STR_ID] = Field(
        default=None, alias="_id", description="Unique identifier for the user"
    )
    username: str = Field(..., description="Username of the user")
    email: str = Field(..., description="Email address of the user")
    provider: Optional[str] = Field(
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
        alias="password",
    )


class UserResponse(UserBase): ...
