from random import randint

from fastapi import Depends
from libgravatar import Gravatar
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.database.models import User
from src.schemas.users import UserModel
from src.services.auth import auth_service


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


async def update_avatar_url(email: str, url: str | None, db: AsyncSession = Depends(get_db)) -> User:
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


async def get_user(user_id: int, db: AsyncSession):#, current_user: User):
    """
    Retrieves a single user with the specified ID for a specific user.

    :param user_id: The ID of the user to retrieve.
    :type user_id: int
    :param db: The async database session.
    :type db: AsyncSession
    :param current_user: The user to retrieve the user for.
    :type current_user: User
    :return: The user with the specified ID, or None if it does not exist.
    :rtype: User | None
    """
    try:
        stmt = select(User).filter_by(id=user_id)#, user=current_user)
        user = await db.execute(stmt)
        return user.scalar_one_or_none()
    except Exception as e:
        print('Error: {e}')