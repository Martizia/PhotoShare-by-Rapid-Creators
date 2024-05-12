from fastapi import HTTPException, status, APIRouter, Depends, Path
from fastapi_limiter.depends import RateLimiter
from src.database.db import get_db
from src.database.models import Role, User
from src.services.auth import auth_service
from src.services.roles import RoleAccess
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.repository import comments as repository_comments
from src.repository import images as repository_images
from src.repository import users as repository_users
from src.repository import rating as repository_rating

from src.schemas.images import ImageResponse
from src.schemas.rating import RatingResponse
from src.schemas.users import UserResponse

CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail='Could not validate credentials',
    headers={'WWW-Authenticate': 'Bearer'},
)

router = APIRouter(prefix='/admin', tags=["For Admins and Moderators"])


@router.put("/users/{email}/role", status_code=status.HTTP_200_OK)
async def change_user_role_by_email(
        email: str,
        new_role: Role,
        current_user: User = Depends(auth_service.get_current_user),
        session: AsyncSession = Depends(get_db),
):
    """
    Changes user role by email

    :param email: Email of the user to change role
    :type email: str
    :param new_role: New role for the user
    :type new_role: Role
    :param current_user: The current user
    :type current_user: User
    :param session: The async database session
    :type session: AsyncSession
    :return: The result of the role change
    :rtype: JSONResponse
    """
    role_access = RoleAccess([Role.admin])
    await role_access(request=None, user=current_user)
    user = await session.execute(select(User).where(User.email == email))
    user = user.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    user.role = new_role
    await session.commit()
    return {"message": "User role updated successfully"}


@router.put("/users/{email}/ban", status_code=status.HTTP_200_OK)
async def ban_user_by_email(
        email: str,
        current_user: User = Depends(auth_service.get_current_user),
        session: AsyncSession = Depends(get_db),
):
    """
    Bans user by email

    :param email: Email of the user to ban
    :type email: str
    :param current_user: The current user
    :type current_user: User
    :param session: The async database session
    :type session: AsyncSession
    :return: The result of the ban
    :rtype: JSONResponse
    """
    role_access = RoleAccess([Role.admin, Role.moderator])
    await role_access(request=None, user=current_user)
    user = await session.execute(select(User).where(User.email == email))
    user = user.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    user.banned = True
    await session.commit()
    return {"message": "User banned successfully"}


@router.put("/users/{email}/unban", status_code=status.HTTP_200_OK)
async def unban_user_by_email(
        email: str,
        current_user: User = Depends(auth_service.get_current_user),
        session: AsyncSession = Depends(get_db),
):
    """
    Unbans user by email

    :param email: Email of the user to unban
    :type email: str
    :param current_user: The current user
    :type current_user: User
    :param session: The async database session
    :type session: AsyncSession
    :return: The result of the unban
    :rtype: JSONResponse
    """
    role_access = RoleAccess([Role.admin, Role.moderator])

    await role_access(request=None, user=current_user)

    user = await session.execute(select(User).where(User.email == email))
    user = user.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    user.banned = False
    await session.commit()

    return {"message": "User unbanned successfully"}


@router.get(
    "/users/{user_id}",
    response_model=UserResponse,
    description="No more than 10 requests per minute",
    dependencies=[Depends(RateLimiter(times=10, seconds=60))]
)
async def get_user_by_id(
        user_id: int = Path(ge=1),
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(auth_service.get_current_user)):
    """
    Returns the user with the given ID. Available only for admin.

    :param user_id: The ID of the user to retrieve.
    :type user_id: int
    :param db: The async database session.
    :type db: AsyncSession
    :param current_user: The currently authenticated user.
    :type current_user: User
    :return: The user with the given ID.
    :rtype: User
    """
    role_access = RoleAccess([Role.admin])
    await role_access(request=None, user=current_user)
    user = await repository_users.get_user_by_id(user_id, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NOT FOUND")
    return user


@router.get("/images/{user_id}", response_model=list[ImageResponse])
async def get_images_by_user_id(user_id: int, db: AsyncSession = Depends(get_db),
                                current_user: User = Depends(auth_service.get_current_user)):
    """
    Gets images by user id. Available for admin and moderator.

    :param user_id: The id of the user.
    :type user_id: int
    :param db: The async database session.
    :type db: AsyncSession
    :param current_user: The current user.
    :type current_user: User
    :return: The list of images.
    :rtype: list[ImageResponse]
    """
    role_access = RoleAccess([Role.admin, Role.moderator])
    await role_access(request=None, user=current_user)
    images = await repository_images.get_images_by_user_id(db, user_id)
    return images


@router.delete("/images/{image_id}")
async def delete_image_admin(image_id: int, db: AsyncSession = Depends(get_db),
                             current_user: User = Depends(auth_service.get_current_user)):
    """
    Deletes the image with the given ID. Available only for admin.

    :param image_id: The ID of the image to delete.
    :type image_id: int
    :param db: The database session.
    :type db: AsyncSession
    :param current_user: The currently authenticated user.
    :type current_user: User
    :return: A message indicating that the image was deleted.
    :rtype: dict
    """
    role_access = RoleAccess([Role.admin])
    await role_access(request=None, user=current_user)
    deleted = await repository_images.delete_image_admin(db, image_id)
    if deleted is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    return {"message": "Image deleted"}


@router.delete(
    "/comments/{comment_id}",
    description="No more than 1 request per 30 seconds",
    dependencies=[Depends(RateLimiter(times=1, seconds=30))],
)
async def delete_comment(
        comment_id: int = Path(ge=1),
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(auth_service.get_current_user),
):
    """
    Deletes a specific comment by its ID. Only admins and moderators can delete comments.

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
    comment = await repository_comments.delete_comment(comment_id, db)
    return comment


@router.get("/ratings/{image_id}", response_model=list[RatingResponse],
            dependencies=[Depends(RateLimiter(times=5, seconds=30))],
            description="No more than 5 requests per 30 seconds")
async def get_image_ratings(image_id: int, db: AsyncSession = Depends(get_db),
                            current_user: User = Depends(auth_service.get_current_user)):
    """
    Get all ratings for an image. Available only for admin and moderator.

    :param image_id: The id of the image.
    :type image_id: int
    :param db: The async database session.
    :type db: AsyncSession
    :param current_user: The current user.
    :type current_user: User
    :return: The list of ratings.
    :rtype: list[RatingResponse]
    """
    role_access = RoleAccess([Role.admin, Role.moderator])
    await role_access(request=None, user=current_user)
    result = await repository_rating.get_image_ratings(db, image_id)
    return result


@router.delete("/ratings/{image_id}")
async def delete_rating(image_id: int, user_id: int, db: AsyncSession = Depends(get_db),
                        current_user: User = Depends(auth_service.get_current_user)):
    """
    Delete a rating by a user for an image. Available only for admin and moderator.

    :param image_id: The id of the image.
    :type image_id: int
    :param user_id: The id of the user.
    :type user_id: int
    :param db: The async database session.
    :type db: AsyncSession
    :param current_user: The current user.
    :type current_user: User
    :return: The deleted rating.
    :rtype: RatingResponse
    """
    role_access = RoleAccess([Role.admin, Role.moderator])
    await role_access(request=None, user=current_user)
    result = await repository_rating.delete_user_rating(db, user_id, image_id)
    return result
