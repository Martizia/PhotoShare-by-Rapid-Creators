from fastapi import Depends
from libgravatar import Gravatar
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import or_

from src.database.db import get_db
from src.database.models import User, Image, Rating

from src.schemas.users import UserModel
from datetime import datetime


async def get_user_by_email(email: str, db: AsyncSession = Depends(get_db)):
    """
    Get user by email

    :param email: The email of the user
    :type email: str
    :param db: The async database session
    :type db: AsyncSession
    :return: The user
    :rtype: User
    """
    stmt = select(User).filter_by(email=email)
    user = await db.execute(stmt)
    user = user.scalar_one_or_none()
    return user


async def create_user(body: UserModel, db: AsyncSession = Depends(get_db)):
    """
    Creates a new user.

    :param body: The data for the new user.
    :type body: UserModel
    :param db: The async database session
    :type db: AsyncSession
    :return: The created user
    :rtype: User
    """
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
    """
    Updates the refresh token for a user.

    :param user: The user to update
    :type user: User
    :param refresh_token: The new refresh token
    :type refresh_token: str | None
    :param db: The async database session
    :type db: AsyncSession
    :return: The updated user
    :rtype: User
    """
    user.refresh_token = refresh_token
    await db.commit()


async def confirmed_email(email: str, db: AsyncSession) -> None:
    """
    Confirms an email.

    :param email: The email to confirm
    :type email: str
    :param db: The async database session
    :type db: AsyncSession
    :return: None
    :rtype: None
    """
    user = await get_user_by_email(email, db)
    user.confirmed = True
    await db.commit()


async def update_avatar_url(email: str, url: str | None, db: AsyncSession) -> User:
    """
    Updates the avatar url for a user.

    :param email: The email of the user
    :type email: str
    :param url: The new avatar url
    :type url: str | None
    :param db: The async database session
    :type db: AsyncSession
    :return: The updated user
    :rtype: User
    """
    user = await get_user_by_email(email, db)
    user.avatar = url
    await db.commit()
    await db.refresh(user)
    return user


async def store_reset_token(email: str, token: str, db: AsyncSession = Depends(get_db)) -> User:
    """
    Stores a reset token for a user.

    :param email: The email of the user
    :type email: str
    :param token: The reset token
    :type token: str
    :param db: The async database session
    :type db: AsyncSession
    :return: The updated user
    :rtype: User
    """
    user = await get_user_by_email(email, db)
    user.reset_token = token
    await db.commit()
    await db.refresh(user)
    return user


async def verify_reset_token(email: str, token: str, db: AsyncSession = Depends(get_db)) -> bool:
    """
    Verifies if a reset token is valid.

    :param email: The email of the user
    :type email: str
    :param token: The reset token
    :type token: str
    :param db: The async database session
    :type db: AsyncSession
    :return: True if the token is valid, False otherwise
    :rtype: bool
    """
    user = await get_user_by_email(email, db)
    if user is not None and user.reset_token == token:
        return True
    return False


async def update_password(email: str, new_password: str, db: AsyncSession = Depends(get_db)) -> User | None:
    """
    Updates the password for a user.

    :param email: The email of the user
    :type email: str
    :param new_password: The new password
    :type new_password: str
    :param db: The async database session
    :type db: AsyncSession
    :return: The updated user
    :rtype: User | None
    """
    from src.services.auth import auth_service
    user = await get_user_by_email(email, db)
    if user is not None:
        hashed_new_password = auth_service.get_password_hash(new_password)
        user.password = hashed_new_password
        await db.commit()
        return user
    return None


async def count_user_images(user_id, db: AsyncSession) -> int:
    """
    Counts the number of images for a user.

    :param user_id: The ID of the user
    :type user_id: int
    :param db: The async database session
    :type db: AsyncSession
    :return: The number of images
    :rtype: int
    """
    stmt = select(Image).where(Image.user_id == user_id)
    result = await db.execute(stmt)
    images = result.scalars().all()
    return len(images)


async def count_user_ratings(user_id, db: AsyncSession) -> int:
    """
    Counts the number of ratings for a user.

    :param user_id: The ID of the user
    :type user_id: int
    :param db: The async database session
    :type db: AsyncSession
    :return: The number of ratings
    :rtype: int
    """
    stmt = select(Rating).where(Rating.user_id == user_id)
    result = await db.execute(stmt)
    images = result.scalars().all()
    return len(images)


async def get_user_by_id(user_id: int, db: AsyncSession) -> User | None:
    """
    Gets a user by ID.

    :param user_id: The ID of the user
    :type user_id: int
    :param db: The async database session
    :type db: AsyncSession
    :return: The user
    :rtype: User | None
    """
    stmt = select(User).filter_by(id=user_id)
    user = await db.execute(stmt)
    result = user.scalar_one_or_none()
    return result


async def update_my_name(
        user: User,
        name: str,
        db: AsyncSession) -> User:
    """
    Updates the name of a user.

    :param user: The user to update the name
    :type user: User
    :param name: The new name for current user
    :type name: str
    :param db: The async database session
    :type db: AsyncSession
    :return: The updated user
    :rtype: User
    """
    user = await get_user_by_id(user.id, db)
    user.username = name
    user.updated_at = datetime.now()
    await db.commit()
    await db.refresh(user)
    return user


async def delete_user(user_id: int, db: AsyncSession) -> dict:
    """
    Deletes a user.

    :param user_id: The ID of the user
    :type user_id: int
    :param db: The async database session
    :type db: AsyncSession
    :return: A dictionary with a message
    :rtype: dict
    """
    stmt = select(User).filter_by(id=user_id)
    user = await db.execute(stmt)
    user = user.scalar_one_or_none()
    if user:
        await db.delete(user)
        await db.commit()
    return {"message": "User deleted"}


async def search_users(search_string: str, db: AsyncSession):
    """
    Searches for users by username or email.

    :param search_string: The string to search for
    :type search_string: str
    :param db: The async database session
    :type db: AsyncSession
    :return: A list of users
    :rtype: list
    """
    query = select(User).filter(
        or_(
            User.username.ilike(f"%{search_string}%"),
            User.email.ilike(f"%{search_string}%")
        )
    ).distinct()
    result = await db.execute(query)
    return result.scalars().all()
