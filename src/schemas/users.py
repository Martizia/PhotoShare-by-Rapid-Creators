from typing import Optional

from pydantic import BaseModel, EmailStr, Field, ConfigDict

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


class UserProfile(BaseModel):
    id: int
    username: str
    email: EmailStr
    avatar: str
    role: Role
    uploaded_images: Optional[int] = None
    rated_images: Optional[int] = None


class UserUpdateMyName(BaseModel):
    username: str


class TokenModel(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RequestEmail(BaseModel):
    email: EmailStr


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordReset(BaseModel):
    token: str
    new_password: str

