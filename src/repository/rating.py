from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Rating, User, Image
from src.schemas.rating import RatingSchema, RatingAverageResponse


async def create_rating(body: RatingSchema, db: AsyncSession, user: User):
    """
    Creates a new rating for a specific user for a specific image.

    :param body: The data for the new rating.
    :type body: RatingSchema
    :param db: The async database session.
    :type db: AsyncSession
    :param user: The user who created the rating.
    :type user: User
    :return: The created rating.
    :rtype: Rating
    """
    new_rating = Rating(**body.model_dump(exclude_unset=True), user_id=user.id)
    if new_rating.rating not in [1, 2, 3, 4, 5]:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Invalid rating value")
    db.add(new_rating)
    await db.commit()
    await db.refresh(new_rating)
    return new_rating


async def get_average_rating_by_image_id(db: AsyncSession, image_id: int) -> RatingAverageResponse:
    """
    Gets the average rating for an image.

    :param db: The async database session.
    :type db: AsyncSession
    :param image_id: The ID of the image.
    :type image_id: int
    :return: The average rating for the image.
    :rtype: RatingAverageResponse
    """
    result = await db.execute(select(
        func.avg(Rating.rating).label("average_rating")
    ).where(Rating.image_id == image_id))
    average_rating = result.scalar()
    if average_rating is None:
        average_rating = 0
    return RatingAverageResponse(image_id=image_id, average_rating=average_rating)


async def get_image(db: AsyncSession, image_id: int):
    """
    Gets an image by ID.

    :param db: The async database session.
    :type db: AsyncSession
    :param image_id: The ID of the image to get.
    :type image_id: int
    :return: The image, or None if it does not exist.
    :rtype: Image | None
    """
    result = await db.execute(select(Image).where(Image.id == image_id))
    rating = result.scalar()
    if not rating:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Image not found")
    return True


async def check_user_rating(db: AsyncSession, user: User, image_id: int):
    """
    Checks if a user has already rated an image.

    :param db: The async database session.
    :type db: AsyncSession
    :param user: The user to check.
    :type user: User
    :param image_id: The ID of the image to check.
    :type image_id: int
    :return: True if the user has already rated the image, False otherwise.
    :rtype: bool
    """
    result = await db.execute(select(Rating).where(
        Rating.user_id == user.id,
        Rating.image_id == image_id
    ))
    rating = result.scalar()
    if rating:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="You have already rated this image")
    return True


async def check_image_owner(db: AsyncSession, user: User, image_id: int):
    """
    Checks if an image owner is the same as the user.

    :param db: The async database session.
    :type db: AsyncSession
    :param user: The user to check.
    :type user: User
    :param image_id: The ID of the image to check.
    :type image_id: int
    :return: True if the image owner is the same as the user, False otherwise.
    :rtype: bool
    """
    result = await db.execute(select(Image).where(
        Image.user_id == user.id,
        Image.id == image_id
    ))
    image = result.scalar()
    if image:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="You cannot rate your own image")
    return True


async def get_image_ratings(db: AsyncSession, image_id: int):
    """
    Gets all ratings for a specific image.

    :param db: The async database session.
    :type db: AsyncSession
    :param image_id: The ID of the image to get ratings for.
    :type image_id: int
    :return: The ratings for the image.
    :rtype: List[Rating]
    """
    result = await db.execute(select(Rating).where(Rating.image_id == image_id))
    return result.scalars().all()


async def delete_user_rating(db: AsyncSession, user_id: int, image_id: int) -> dict:
    """
    Deletes a rating for an image.

    :param db: The async database session.
    :type db: AsyncSession
    :param user_id: The ID of the user.
    :type user_id: int
    :param image_id: The ID of the image.
    :type image_id: int
    :return: The message that the rating was deleted.
    :rtype: dict
    """
    result = await db.execute(select(Rating).where(
        Rating.user_id == user_id,
        Rating.image_id == image_id
    ))
    rating = result.scalar()
    if not rating:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Rating not found")
    await db.delete(rating)
    await db.commit()
    return {"message": "Rating deleted successfully"}
