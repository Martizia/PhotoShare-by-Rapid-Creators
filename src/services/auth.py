import pickle
from datetime import datetime, timedelta, timezone
from typing import Optional

import redis
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.config import config
from src.database.db import get_db
from src.database.models import Role
from src.repository import users as repository_users

from passlib.context import CryptContext


CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail='Could not validate credentials',
    headers={'WWW-Authenticate': 'Bearer'},
)


class Auth:
    """
    Class handles authentication and authorization
    """
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    now_utc = datetime.now(timezone.utc)
    SECRET_KEY = config.SECRET_KEY_JWT
    ALGORITHM = config.ALGORITHM
    cache = redis.Redis(host=config.REDIS_DOMAIN, port=config.REDIS_PORT, db=0, password=config.REDIS_PASSWORD)

    def verify_password(self, plain_password, hashed_password):
        """
        Verify password using hashing

        :param plain_password: password provided by user
        :type plain_password: str
        :param hashed_password: hashed password from database
        :type hashed_password: str
        :return: True if passwords match else False
        :rtype: bool
        """
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str):
        """
        Hash password using bcrypt

        :param password: password provided by user
        :type password: str
        :return: hashed password
        :rtype: str
        """
        return self.pwd_context.hash(password)

    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

    async def create_access_token(self, data: dict, expires_delta: Optional[float] = None):
        """
        Create access token

        :param data: data to encode
        :type data: dict
        :param expires_delta: expiration time in seconds
        :type expires_delta: float
        :return: encoded access token
        :rtype: str
        """
        to_encode = data.copy()
        if expires_delta:
            expire = self.now_utc + timedelta(seconds=expires_delta)
        else:
            expire = self.now_utc + timedelta(minutes=60)
        to_encode.update({"iat": self.now_utc, "exp": expire, "scope": "access_token"})
        encoded_access_token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return encoded_access_token

    async def create_refresh_token(self, data: dict, expires_delta: Optional[float] = None):
        """
        Create refresh token

        :param data: data to encode
        :type data: dict
        :param expires_delta: expiration time in seconds
        :type expires_delta: float
        :return: encoded refresh token
        :rtype: str
        """
        to_encode = data.copy()
        if expires_delta:
            expire = self.now_utc + timedelta(seconds=expires_delta)
        else:
            expire = self.now_utc + timedelta(days=7)
        to_encode.update({"iat": self.now_utc, "exp": expire, "scope": "refresh_token"})
        encoded_refresh_token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return encoded_refresh_token

    async def decode_refresh_token(self, refresh_token: str):
        """
        Decode refresh token

        :param refresh_token: refresh token provided by user
        :type refresh_token: str
        :return: email of user
        :rtype: str
        """
        try:
            payload = jwt.decode(refresh_token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            if payload['scope'] == 'refresh_token':
                email = payload['sub']
                return email
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid scope for token')
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate credentials')

    async def get_current_user(self, token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
        """
        Get current user from token

        :param token: access token provided by user
        :type token: str
        :param db: database session
        :type db: AsyncSession
        :return: user object
        :rtype: User
        """
        if is_token_blacklisted(token):
            raise CREDENTIALS_EXCEPTION
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            if payload['scope'] == 'access_token':
                email = payload["sub"]
                if email is None:
                    raise credentials_exception
            else:
                raise credentials_exception
        except JWTError as e:
            raise e

        user_hash = str(email)
        user = self.cache.get(user_hash)

        if user is None:
            user = await repository_users.get_user_by_email(email, db)
            if user is None:
                raise credentials_exception
            self.cache.set(user_hash, pickle.dumps(user))  # noqa
            self.cache.expire(user_hash, 300)  # noqa
        else:
            user = pickle.loads(user)  # noqa
        return user

    def create_email_token(self, data: dict):
        """
        Create email token for verification email

        :param data: data to encode
        :type data: dict
        :return: encoded token
        :rtype: str
        """
        to_encode = data.copy()
        expire = self.now_utc + timedelta(days=1)
        to_encode.update({"iat": self.now_utc, "exp": expire})
        token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return token

    async def get_email_from_token(self, token: str):
        """
        Get email from token for verification email

        :param token: token provided by user
        :type token: str
        :return: email of user
        :rtype: str
        """
        if is_token_blacklisted(token):
            raise CREDENTIALS_EXCEPTION
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            email = payload["sub"]
            return email
        except JWTError as e:
            print(e)
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail="Invalid token for email verification")

    async def get_current_user_token(self, token: str = Depends(oauth2_scheme)):
        """
        Get current user from token

        :param token: access token provided by user
        :type token: str
        :return: user object
        :rtype: User
        """
        return token


def init_blacklist_file():
    """
    Initialize blacklist file.

    :return: True if file is created
    :rtype: bool
    """
    open('blacklist_db.txt', 'a').close()
    return True


def add_blacklist_token(token):
    """
    Add token to blacklist.

    :param token: token to blacklist
    :type token: str
    :return: True if token is added to blacklist
    :rtype: bool
    """
    with open('blacklist_db.txt', 'a') as file:
        file.write(f'{token},')
    return True


def is_token_blacklisted(token):
    """
    Check if token is in blacklist.

    :param token: token to check
    :type token: str
    :return: True if token is in blacklist
    :rtype: bool
    """
    with open('blacklist_db.txt') as file:
        content = file.read()
        array = content[:-1].split(',')
        for value in array:
            if value == token:
                return True

    return False


auth_service = Auth()
