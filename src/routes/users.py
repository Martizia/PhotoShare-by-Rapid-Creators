import cloudinary
import cloudinary.uploader
from fastapi import APIRouter, Depends, File, UploadFile, Path, status, HTTPException
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.config import config
from src.database.db import get_db
from src.database.models import User
from src.repository import users as repository_users
from src.schemas.users import UserResponse
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
async def upload_avatar(file: UploadFile = File(),
                        user: User = Depends(auth_service.get_current_user),
                        db: AsyncSession = Depends(get_db)):
    public_id = f"Application/{user.email}"
    image = cloudinary.uploader.upload(file.file, public_id=public_id, overwrite=True)
    print(image)
    image_url = cloudinary.CloudinaryImage(public_id).build_url(width=250, height=250, crop=True,
                                                                version=image.get('version'))
    user = await repository_users.update_avatar_url(user.email, image_url, db)
    return user


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    description="No more than 10 requests per minute",
    dependencies=[Depends(RateLimiter(times=10, seconds=60))],
)
async def get_user(
    user_id: int = Path(ge=1),
    db: AsyncSession = Depends(get_db),):
    #current_user: User = Depends(auth_service.get_current_user),):
    """
    Retrieves a specific user by its ID for the authenticated user.

    :param user_id: The ID of the user to retrieve. Must be greater than or equal to 1.
    :type user_id: int
    :param db: The database session.
    :type db: AsyncSession
    :param current_user: The currently authenticated user.
    :type current_user: User

    :raises HTTPException: If the user is not found.

    :return: The user with the specified ID.
    :rtype: User
    """
    user = await repository_users.get_user(user_id, db)#, current_user)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NOT FOUND")
    return user