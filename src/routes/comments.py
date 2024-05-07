from fastapi import APIRouter, Depends, Path, status, HTTPException
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.database.models import User, Role
from src.repository import comments as repository_comments
from src.schemas.comments import CommentModel, CommentUpdateSchema
from src.services.auth import auth_service
from src.repository.rating import get_image
from src.services.roles import RoleAccess

router = APIRouter(prefix='/comments', tags=["comments"])


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
    await get_image(db, body.image_id)
    if body is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Comment is empty")
    comment = await repository_comments.create_comment(body, db, current_user)
    return comment
    

@router.put(
    "/{comment_id}",
    description="No more than 3 requests per minute",
    dependencies=[Depends(RateLimiter(times=3, seconds=60))],
)
async def update_comment(
    body: CommentUpdateSchema,
    comment_id: int = Path(ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
):
    """
    Updates a specific comment by its ID for the authenticated user.

    :param body: The updated data for the comment.
    :type body: CommentUpdateSchema
    :param comment_id: The ID of the comment to update. Must be greater than or equal to 1.
    :type comment_id: int
    :param db: The database session.
    :type db: AsyncSession
    :param current_user: The currently authenticated user.
    :type current_user: User

    :raises HTTPException: If the comment is not found.

    :return: The updated comment.
    :rtype: Comment
    """
    comment = await repository_comments.update_comment(
        comment_id, body, db, current_user
    )
    if comment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NOT FOUND")
    return comment


@router.delete(
    "/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    description="No more than 1 request per minute",
    dependencies=[Depends(RateLimiter(times=1, seconds=60))],
)
async def delete_comment(
    comment_id: int = Path(ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_service.get_current_user),
):
    """
    Deletes a specific comment by its ID for the authenticated user.

    :param comment_id: The ID of the comment to delete. Must be greater than or equal to 1.
    :type comment_id: int
    :param db: The database session.
    :type db: AsyncSession
    :param current_user: The currently authenticated user.
    :type current_user: User

    :return: The deleted comment.
    :rtype: Comment
    """
    role_access = RoleAccess([Role.admin, Role.moderator])
    await role_access(request=None, user=current_user)
    comment = await repository_comments.delete_comment(comment_id, db, current_user)
    return comment
