from random import randint

from fastapi import Depends
from libgravatar import Gravatar
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.database.models import User
from src.schemas.users import UserModel, UserUpdateMyAcount, UserUpdateByAdmin
#from src.services.auth import auth_service
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


async def update_my_acount(
        user: User,
        body: UserUpdateMyAcount,
        db: AsyncSession):
    """
    Updates a single user with the specified ID for a specific user.

    :param user_id: The ID of the user to update.
    :type user_id: int
    :param body: The updated data for the user.
    :type body: UserUpdate
    :param db: The async database session.
    :type db: AsyncSession
    :param current_user: The user to update the user for.
    :type current_user: User
    :return: The updated user, or None if it does not exist.
    :rtype: User | None
    """
    if user:
        if user.username != body.username:
            if body.username != 'string':
                user.username = body.username
        if user.email != body.email:
            if body.email != "user@example.com":
                user.email = body.email
        if user.avatar != body.avatar:
            if body.avatar != 'string':
                user.avatar = body.avatar
        if user.role != body.role:
            user.role= body.role
        user.updated_at=datetime.now()
        await db.commit()
        await db.refresh(user)
    return user


async def update_user_by_admin(
        user_id: int,
        body: UserUpdateByAdmin,
        db: AsyncSession):
    """
    Updates a single user with the specified ID for a specific user.

    :param user_id: The ID of the user to update.
    :type user_id: int
    :param body: The updated data for the user.
    :type body: UserUpdate
    :param db: The async database session.
    :type db: AsyncSession
    :param current_user: The user to update the user for.
    :type current_user: User
    :return: The updated user, or None if it does not exist.
    :rtype: User | None
    """
    
    stmt = select(User).filter_by(id=user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    if user:
        print('32214134', user.username, body.username)

        if user.username != body.username:
            if body.username != 'string':
                user.username = body.username
        if user.email != body.email:
            if body.email != "user@example.com":
                user.email = body.email
        if user.password != body.password:
            if body.avatar != 'string':
                user.password = body.password
        if user.avatar != body.avatar:
            if body.avatar != 'string':
                user.avatar = body.avatar
        user.updated_at=datetime.now()
        if user.role != body.role:
            user.role= body.role
        if user.confirmed != body.confirmed:
            user.confirmed= body.confirmed
        if user.banned != body.banned:
            user.banned= body.banned
        await db.commit()
        await db.refresh(user)
    return user


async def delete_user(user_id: int, db: AsyncSession):#, current_user: User):
    """
    Removes a single user with the specified ID for a specific user.

    :param user_id: The ID of the user to remove.
    :type user_id: int
    :param db: The async database session.
    :type db: AsyncSession
    :param current_user: The user to remove the user for.
    :type current_user: User
    :return: The removed user, or None if it does not exist.
    :rtype: User | None
    """
    stmt = select(User).filter_by(id=user_id)#, user=current_user)
    user = await db.execute(stmt)
    user = user.scalar_one_or_none()
    if user:
        await db.delete(user)
        await db.commit()
    return user
