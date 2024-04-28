from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import select, or_, extract, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Rating, User, Image
from src.schemas.rating import RatingSchema, RatingResponse, RatingAverageResponse


async def get_current_user(db: AsyncSession, user_id: int):
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar()


async def get_current_image(db: AsyncSession, image_id: int):
    result = await db.execute(select(Image).where(Image.id == image_id))
    return result.scalar()


async def create_rating(body: RatingSchema, db: AsyncSession, user: int, image: int):
    new_rating = Rating(**body.model_dump(exclude_unset=True))
    new_rating.user_id = user
    new_rating.image_id = image
    new_rating.created_at = datetime.now(timezone.utc).replace(tzinfo=None)
    if new_rating.rating not in [1, 2, 3, 4, 5]:
        raise HTTPException(status_code=400, detail="Invalid rating value")
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
