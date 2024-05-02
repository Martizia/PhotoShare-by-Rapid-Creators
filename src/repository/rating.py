from fastapi import HTTPException, status
from sqlalchemy import select, or_, extract, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Rating, User, Image, Role
from src.schemas.rating import RatingSchema, RatingResponse, RatingAverageResponse


async def create_rating(body: RatingSchema, db: AsyncSession, user: User):
    new_rating = Rating(**body.model_dump(exclude_unset=True), user=user)
    if new_rating.rating not in [1, 2, 3, 4, 5]:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Invalid rating value")
    db.add(new_rating)
    await db.commit()
    await db.refresh(new_rating)
    return new_rating


async def get_average_rating_by_image_id(db: AsyncSession, image_id: int) -> RatingAverageResponse:
    result = await db.execute(select(
        func.avg(Rating.rating).label("average_rating")
    ).where(Rating.image_id == image_id))
    average_rating = result.scalar()
    if average_rating is None:
        average_rating = 0
    return RatingAverageResponse(image_id=image_id, average_rating=average_rating)


async def check_user_rating(db: AsyncSession, user: User, image_id: int):
    result = await db.execute(select(Rating).where(
        Rating.user_id == user.id,
        Rating.image_id == image_id
    ))
    rating = result.scalar()
    if image_id != Image.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Image not found")
    if rating:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="You have already rated this image")
    return True


async def check_image_owner(db: AsyncSession, user: User, image_id: int):
    result = await db.execute(select(Image).where(
        Image.user_id == user.id,
        Image.id == image_id
    ))
    image = result.scalar()
    if image:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="You cannot rate your own image")
    return True


async def check_user_role(db: AsyncSession, user: User):
    result = await db.execute(select(User).where(User.id == user.id))
    user_db = result.scalar()
    if user_db.role == Role.user:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="You do not have enough permissions")
    return True


async def get_image_ratings(db: AsyncSession, image_id: int):
    result = await db.execute(select(Rating).where(Rating.image_id == image_id))
    return result.scalars().all()


async def delete_user_rating(db: AsyncSession, user_id: int, image_id: int):
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