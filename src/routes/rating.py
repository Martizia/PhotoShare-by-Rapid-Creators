from fastapi import APIRouter, HTTPException, Depends, status, Path, Query
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.database.models import Rating, User, Image
from src.repository import rating as repository_rating
from src.schemas.rating import RatingResponse, RatingSchema, RatingAverageResponse

router = APIRouter(prefix="/rating", tags=["rating"])


@router.post("/", response_model=RatingResponse, status_code=status.HTTP_201_CREATED)
async def create_rating(body: RatingSchema, db: AsyncSession = Depends(get_db)
                        ):
    rating = await repository_rating.create_rating(body, db, body.user_id, body.image_id)
    return rating


@router.get("/{image_id}", response_model=RatingAverageResponse)
async def get_average_rating(image_id: int, db: AsyncSession = Depends(get_db)):
    rating = await repository_rating.get_average_rating_by_image_id(db, image_id)
    return rating
