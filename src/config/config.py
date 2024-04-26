from os import environ
from pathlib import Path
from typing import Dict
from dotenv import load_dotenv
from pydantic import ConfigDict, field_validator, EmailStr
from pydantic_settings import BaseSettings


BASE_PATH_PROJECT = Path(__file__).resolve().parent.parent
# print(f"{BASE_PATH_PROJECT=}")
BASE_PATH = BASE_PATH_PROJECT.parent
# print(f"{BASE_PATH=}")
load_dotenv(BASE_PATH.joinpath(".env"))
APP_ENV = environ.get("APP_ENV")
# print(f"{APP_ENV=}")

class Settings(BaseSettings):
    APP_NAME: str
    APP_MODE: str
    DATABASE_URL: str
    SECRET_KEY_JWT: str
    ALGORITHM: str
    MAIL_USERNAME: EmailStr
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int
    MAIL_SERVER: str
    REDIS_DOMAIN: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str | None = None
    CLOUDINARY_NAME: str
    CLOUDINARY_API_KEY: int
    CLOUDINARY_API_SECRET: str
    STATIC_DIRECTORY: str = str(BASE_PATH_PROJECT.joinpath("static"))

    @field_validator("ALGORITHM")
    @classmethod
    def validate_algorithm(cls, v):
        if v not in ["HS256", "HS512"]:
            raise ValueError("Algorithm must be HS256 or HS512")
        return v

    model_config = ConfigDict(
        extra="ignore",
        env_file=BASE_PATH.joinpath(".env"),
        env_file_encoding="utf-8",
    )


config = Settings()
