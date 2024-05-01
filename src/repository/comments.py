from random import randint

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.database.models import User, Comment
from src.schemas.comments import CommentModel
# import pytz

# utc_timezone = pytz.timezone('UTC')


async def create_comment(body: CommentModel, db: AsyncSession, current_user: User):
    """
    Creates a new contact for a specific user.

    :param body: The data for the contact to create.
    :type body: CommentModel
    :param db: The async database session.
    :type db: AsyncSession
    :param current_user: The user to create the contact for.
    :type current_user: User
    :return: The newly created contact.
    :rtype: Comment
    """
    # print('Body', body)
    # print('Body - created_at.', body.created_at)
    # print('Body - updated_at', body.updated_at)
    # body.created_at.replace(tzinfo=None)
    # body.updated_at.replace(tzinfo=None)
    # print('Body - created_at.', body.created_at)
    # print('Body - updated_at', body.updated_at)

    contact = Comment(**body.model_dump(exclude_unset=True), user_id=current_user.id)
    db.add(contact)
    await db.commit()
    await db.refresh(contact)
    return contact