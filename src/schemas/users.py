from pydantic import BaseModel, EmailStr, Field, ConfigDict

from sqlalchemy import DateTime, func
from datetime import datetime

from src.database.models import Role


class UserModel(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=6, max_length=10)


class UserResponse(BaseModel):
    id: int = 1
    username: str
    email: EmailStr
    avatar: str
    role: Role
    model_config = ConfigDict(from_attributes=True)


class UserUpdateByAdmin(BaseModel):
    username: str | None = Field(default=None)
    email: EmailStr
    password: str | None = Field(default=None, min_length=6, max_length=10)
    avatar: str | None = Field(default=None)
    updated_at: datetime | None
    role: Role | None = Field(default=None,examples=["user"] )
    confirmed: bool | None = Field(default=None, examples=[False])
    banned: bool | None = Field(default=None, examples=[False])


class UserUpdateMyAcount(BaseModel):
    username: str
    email: EmailStr
    avatar: str
    role: Role
    model_config: ConfigDict = ConfigDict(from_attributes=True)
    updated_at: datetime | None


class TokenModel(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RequestEmail(BaseModel):
    email: EmailStr


class PasswordResetRequest(BaseModel):
    email: str


class PasswordReset(BaseModel):
    token: str
    new_password: str

