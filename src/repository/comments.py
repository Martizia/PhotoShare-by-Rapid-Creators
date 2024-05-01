from random import randint

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.database.models import User, Comment
from src.schemas.comments import CommentModel, CommentUpdateSchema
# import pytz

# utc_timezone = pytz.timezone('UTC')


async def create_comment(body: CommentModel, db: AsyncSession, current_user: User):
    """
    Creates a new comment for a specific user.

    :param body: The data for the comment to create.
    :type body: CommentModel
    :param db: The async database session.
    :type db: AsyncSession
    :param current_user: The user to create the comment for.
    :type current_user: User
    :return: The newly created comment.
    :rtype: Comment
    """
    # print('Body', body)
    # print('Body - created_at.', body.created_at)
    # print('Body - updated_at', body.updated_at)
    # body.created_at.replace(tzinfo=None)
    # body.updated_at.replace(tzinfo=None)
    # print('Body - created_at.', body.created_at)
    # print('Body - updated_at', body.updated_at)

    comment = Comment(**body.model_dump(exclude_unset=True), user_id=current_user.id)
    db.add(comment)
    await db.commit()
    await db.refresh(comment)
    return comment


async def update_comment(
        comment_id: int, body: CommentUpdateSchema, db: AsyncSession, current_user: User):
    """
    Updates a single comment with the specified ID for a specific user.

    :param comment_id: The ID of the comment to update.
    :type comment_id: int
    :param body: The updated data for the comment.
    :type body: CommentUpdateSchema
    :param db: The async database session.
    :type db: AsyncSession
    :param current_user: The user to update the comment for.
    :type current_user: User
    :return: The updated comment, or None if it does not exist.
    :rtype: Comment | None
    """ 
    stmt = select(Comment).filter_by(id=comment_id, user_id=current_user.id)
    result = await db.execute(stmt)
    comment = result.scalar_one_or_none()
    if comment:
        comment.text = body.text
        await db.commit()
        await db.refresh(comment)
    return comment




async def delete_comment(comment_id: int, db: AsyncSession, current_user: User):
    """
    Removes a single comment with the specified ID for a specific user.

    :param comment_id: The ID of the comment to remove.
    :type comment_id: int
    :param db: The async database session.
    :type db: AsyncSession
    :param current_user: The user to remove the comment for.
    :type current_user: User
    :return: The removed comment, or None if it does not exist.
    :rtype: Comment | None
    """
    stmt = select(Comment).filter_by(id=comment_id, user_id=current_user.id)
    comment = await db.execute(stmt)
    comment = comment.scalar_one_or_none()
    if comment:
        await db.delete(comment)
        await db.commit()
    return comment