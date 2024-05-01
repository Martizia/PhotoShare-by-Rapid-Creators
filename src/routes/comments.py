import cloudinary
import cloudinary.uploader
from fastapi import APIRouter, Depends, File, UploadFile, Path, status, HTTPException
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.database.models import User
from src.repository import comments as repository_comments
from src.schemas.comments import CommentModel
from src.services.auth import auth_service

router = APIRouter(prefix='/comments', tags=["commentss"])


@router.post(
    '/',
    response_model=CommentModel,
    status_code=status.HTTP_201_CREATED,
    description="No more than 5 requests per minute",
    dependencies=[Depends(RateLimiter(times=5, seconds=60))],
)
async def create_comment(
    body: CommentModel = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
):
    """
    Creates a new comment for the authenticated user.

    :param body: The data for the new comment.
    :type body: CommentSchema
    :param db: The database session.
    :type db: AsyncSession
    :param current_user: The currently authenticated user.
    :type current_user: User

    :return: The newly created comment.
    :rtype: Comment
    """
    if body is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NO Commnet")
    else:
        comment = await repository_comments.create_comment(body, db, current_user)
        return comment