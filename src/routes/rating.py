from fastapi import APIRouter, HTTPException, Depends, status
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.database.models import Rating, User, Image
from src.repository import rating as repository_rating
from src.schemas.rating import RatingResponse, RatingSchema, RatingAverageResponse
from src.services.auth import auth_service

router = APIRouter(prefix="/rating", tags=["rating"])


@router.post("/", response_model=RatingResponse, status_code=status.HTTP_201_CREATED)
async def create_rating(body: RatingSchema, db: AsyncSession = Depends(get_db),
                        user: User = Depends(auth_service.get_current_user),
                        ):
    await repository_rating.check_user_rating(db, user, body.image_id)
    await repository_rating.check_image_owner(db, user, body.image_id)
    rating = await repository_rating.create_rating(body, db, user)
    return rating


@router.get("/average/{image_id}", response_model=RatingAverageResponse)
async def get_average_rating(image_id: int, db: AsyncSession = Depends(get_db),
                             user: User = Depends(auth_service.get_current_user)):
    rating = await repository_rating.get_average_rating_by_image_id(db, image_id)
    return rating


@router.get("/{image_id}", response_model=list[RatingResponse])
async def get_image_ratings(image_id: int, db: AsyncSession = Depends(get_db),
                            user: User = Depends(auth_service.get_current_user)):
    await repository_rating.check_user_role(db, user)
    result = await repository_rating.get_image_ratings(db, image_id)
    return result


@router.delete("/{image_id}")
async def delete_rating(image_id: int, user_id: int, db: AsyncSession = Depends(get_db),
                        user: User = Depends(auth_service.get_current_user)):
    await repository_rating.check_user_role(db, user)
    result = await repository_rating.delete_user_rating(db, user_id, image_id)
    return result
