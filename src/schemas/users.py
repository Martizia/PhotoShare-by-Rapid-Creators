from pydantic import BaseModel, EmailStr, Field, ConfigDict
from sqlalchemy import DateTime, func
from datetime import datetime

from src.database.models import Role


class UserModel(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=6, max_length=8)


class UserResponse(BaseModel):
    id: int = 1
    username: str
    email: EmailStr
    avatar: str
    role: Role
    model_config = ConfigDict(from_attributes=True)


# class UserUpdateSchema(BaseModel):
#     username: str
#     email: EmailStr
#     avatar: str
#     role: Role
#     model_config: ConfigDict = ConfigDict(from_attributes=True)
#     updated_at: DateTime = datetime.now()
#     banned: bool

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
