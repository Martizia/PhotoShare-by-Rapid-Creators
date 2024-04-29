from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import select, or_, extract, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Rating, User, Image
from src.schemas.rating import RatingSchema, RatingResponse, RatingAverageResponse


async def create_rating(body: RatingSchema, db: AsyncSession, user: User):
    new_rating = Rating(**body.model_dump(exclude_unset=True), user_id=user)
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
