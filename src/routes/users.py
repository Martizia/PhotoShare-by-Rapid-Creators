import cloudinary
import cloudinary.uploader
from fastapi import APIRouter, Depends, File, UploadFile, Path, status, HTTPException
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.config import config
from src.database.db import get_db
from src.database.models import User
from src.repository import users as repository_users
from src.schemas.users import UserResponse, UserUpdateMyName
from src.services.auth import auth_service

router = APIRouter(prefix='/users', tags=["users"])

cloudinary.config(cloud_name=config.CLOUDINARY_NAME,
                  api_key=config.CLOUDINARY_API_KEY,
                  api_secret=config.CLOUDINARY_API_SECRET,
                  secure=True)


@router.get('/me', response_model=UserResponse, dependencies=[Depends(RateLimiter(times=1, seconds=20))])
async def get_my_user(my_user: User = Depends(auth_service.get_current_user)):
    return my_user


@router.patch('/avatar', response_model=UserResponse, dependencies=[Depends(RateLimiter(times=1, seconds=20))])
async def change_avatar(file: UploadFile = File(),
                        user: User = Depends(auth_service.get_current_user),
                        db: AsyncSession = Depends(get_db)):
    public_id = f"Application/{user.email}"
    image = cloudinary.uploader.upload(file.file, public_id=public_id, overwrite=True)
    image_url = cloudinary.CloudinaryImage(public_id).build_url(width=250, height=250, crop='fill',
                                                                version=image.get('version'))
    user = await repository_users.update_avatar_url(user.email, image_url, db)
    return user


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    description="No more than 10 requests per minute",
    dependencies=[Depends(RateLimiter(times=10, seconds=60))],
)
async def get_user_by_id(
    user_id: int = Path(ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_service.get_admin)):
    user = await repository_users.get_user_by_id(user_id, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NOT FOUND")
    return user


@router.put(
    "/{user_id}",
    description="No more than 3 requests per minute",
    dependencies=[Depends(RateLimiter(times=3, seconds=60))],
)
async def update_my_name(
    name: str,
    user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user = await repository_users.update_my_name(user, name, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NOT FOUND")
    return user


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    description="No more than 1 request per minute",
    dependencies=[Depends(RateLimiter(times=1, seconds=60))],
)
async def delete_user(
    user_id: int = Path(ge=1),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(auth_service.get_admin)):
    user = await repository_users.delete_user(user_id, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NOT FOUND")
    return user

