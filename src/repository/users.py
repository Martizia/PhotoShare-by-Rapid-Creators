from random import randint
from fastapi import Depends
from libgravatar import Gravatar
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.database.models import User

from src.schemas.users import UserModel, UserUpdateMyName
from datetime import datetime


async def get_user_by_email(email: str, db: AsyncSession = Depends(get_db)):
    stmt = select(User).filter_by(email=email)
    user = await db.execute(stmt)
    user = user.scalar_one_or_none()
    return user


async def create_user(body: UserModel, db: AsyncSession = Depends(get_db)):
    avatar = None
    try:
        g = Gravatar(body.email)
        avatar = g.get_image()
    except Exception as err:
        print(err)

    new_user = User(**body.model_dump(), avatar=avatar)
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


async def update_token(user: User, refresh_token: str | None, db: AsyncSession = Depends(get_db)):
    user.refresh_token = refresh_token
    await db.commit()


async def confirmed_email(email: str, db: AsyncSession) -> None:
    user = await get_user_by_email(email, db)
    user.confirmed = True
    await db.commit()


async def update_avatar_url(email: str, url: str | None, db: AsyncSession) -> User:
    user = await get_user_by_email(email, db)
    user.avatar = url
    await db.commit()
    await db.refresh(user)
    return user


async def store_reset_token(email: str, token: str, db: AsyncSession = Depends(get_db)):
    user = await get_user_by_email(email, db)
    user.reset_token = token
    await db.commit()
    await db.refresh(user)
    return user


async def verify_reset_token(email: str, token: str, db: AsyncSession = Depends(get_db)):
    user = await get_user_by_email(email, db)
    if user is not None and user.reset_token == token:
        return True
    return False


async def update_password(email: str, new_password: str, db: AsyncSession = Depends(get_db)):
    from src.services.auth import auth_service
    user = await get_user_by_email(email, db)
    if user is not None:
        hashed_new_password = auth_service.get_password_hash(new_password)
        user.password = hashed_new_password
        await db.commit()
        return user
    return None


async def get_user_by_id(user_id: int, db: AsyncSession):
    stmt = select(User).filter_by(id=user_id)
    user = await db.execute(stmt)
    result = user.scalar_one_or_none()
    return result


async def update_my_name(
        user: User,
        name: str,
        db: AsyncSession):
    user = await get_user_by_id(user.id, db)
    user.username = name
    user.updated_at = datetime.now()
    await db.commit()
    await db.refresh(user)
    return user


async def delete_user(user_id: int, db: AsyncSession):
    stmt = select(User).filter_by(id=user_id)
    user = await db.execute(stmt)
    user = user.scalar_one_or_none()
    if user:
        await db.delete(user)
        await db.commit()
    return f'{user.username} deleted'

