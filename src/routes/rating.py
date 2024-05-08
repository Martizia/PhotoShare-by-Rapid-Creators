from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi_limiter.depends import RateLimiter
from src.database.db import get_db
from src.database.models import User, Role
from src.repository import rating as repository_rating
from src.schemas.rating import RatingResponse, RatingSchema, RatingAverageResponse
from src.services.auth import auth_service
from src.services.roles import RoleAccess

router = APIRouter(prefix="/rating", tags=["Rating"])


@router.post("/", response_model=RatingResponse, status_code=status.HTTP_201_CREATED,
             dependencies=[Depends(RateLimiter(times=5, seconds=30))],
             description="No more than 5 requests per 30 seconds")
async def create_rating(body: RatingSchema, db: AsyncSession = Depends(get_db),
                        current_user: User = Depends(auth_service.get_current_user),
                        ):
    """
    Create a new rating for an image by a current user.

    :param body: The data for the new rating.
    :type body: RatingSchema
    :param db: The async database session.
    :type db: AsyncSession
    :param current_user: The current user.
    :type current_user: User
    :return: The created rating.
    :rtype: RatingResponse
    """
    await repository_rating.get_image(db, body.image_id)
    await repository_rating.check_user_rating(db, current_user, body.image_id)
    await repository_rating.check_image_owner(db, current_user, body.image_id)
    rating = await repository_rating.create_rating(body, db, current_user)
    return rating


@router.get("/average/{image_id}", response_model=RatingAverageResponse,
            dependencies=[Depends(RateLimiter(times=5, seconds=30))],
            description="No more than 5 requests per 30 seconds")
async def get_average_rating(image_id: int, db: AsyncSession = Depends(get_db),
                             current_user: User = Depends(auth_service.get_current_user)):
    """
    Get the average rating for an image by a current user.

    :param image_id: The id of the image.
    :type image_id: int
    :param db: The async database session.
    :type db: AsyncSession
    :param current_user: The current user.
    :type current_user: User
    :return: The average rating.
    :rtype: RatingAverageResponse
    """
    rating = await repository_rating.get_average_rating_by_image_id(db, image_id)
    return rating


@router.get("/{image_id}", response_model=list[RatingResponse],
            dependencies=[Depends(RateLimiter(times=5, seconds=30))],
            description="No more than 5 requests per 30 seconds")
async def get_image_ratings(image_id: int, db: AsyncSession = Depends(get_db),
                            current_user: User = Depends(auth_service.get_current_user)):
    """
    Get all ratings for an image by a current user. Available only for admin and moderator.

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


@router.delete("/{image_id}")
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
