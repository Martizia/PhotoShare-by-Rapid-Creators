import cloudinary
import cloudinary.uploader
from fastapi import APIRouter, Depends, File, UploadFile, Path, status, HTTPException
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.config import config
from src.database.db import get_db
from src.database.models import User, Role
from src.repository import users as repository_users
from src.schemas.users import UserResponse, UserProfile
from src.services.auth import auth_service
from src.services.roles import RoleAccess

router = APIRouter(prefix='/users', tags=["Users"])

cloudinary.config(cloud_name=config.CLOUDINARY_NAME,
                  api_key=config.CLOUDINARY_API_KEY,
                  api_secret=config.CLOUDINARY_API_SECRET,
                  secure=True)


@router.get('/me', response_model=UserProfile, dependencies=[Depends(RateLimiter(times=1, seconds=10))],
            description="No more than 1 request per 10 seconds")
async def get_my_user(my_user: User = Depends(auth_service.get_current_user), db: AsyncSession = Depends(get_db)):
    """
    Returns the profile of the currently authenticated user.

    :param my_user: The currently authenticated user.
    :type my_user: User
    :param db: The async database session.
    :type db: AsyncSession
    :return: The profile of the currently authenticated user.
    :rtype: UserProfile
    """
    my_user = UserProfile(
        id=my_user.id,
        username=my_user.username,
        email=my_user.email,
        avatar=my_user.avatar,
        role=my_user.role
    )
    my_user.uploaded_images = await repository_users.count_user_images(my_user.id, db)
    my_user.rated_images = await repository_users.count_user_ratings(my_user.id, db)
    return my_user


@router.patch('/avatar', response_model=UserResponse, dependencies=[Depends(RateLimiter(times=1, seconds=20))],
              description="No more than 1 request per 20 seconds")
async def change_avatar(file: UploadFile = File(...),
                        user: User = Depends(auth_service.get_current_user),
                        db: AsyncSession = Depends(get_db)):
    """
    Changes the avatar of the currently authenticated user.

    :param file: The file to upload.
    :type file: UploadFile
    :param user: The currently authenticated user.
    :type user: User
    :param db: The async database session.
    :type db: AsyncSession
    :return: The updated user.
    :rtype: User
    """
    max_size = 3 * 1024 * 1024  # 3MB in bytes
    file_content = await file.read()
    file_size = len(file_content)
    if file_size == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File is empty")
    if file_size > max_size:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File size exceeds 3MB")
    public_id = f"Application/{user.email}"
    image = cloudinary.uploader.upload(file_content, public_id=public_id, overwrite=True)
    image_url = cloudinary.CloudinaryImage(public_id).build_url(width=250, height=250, crop='fill',
                                                                version=image.get('version'))
    user = await repository_users.update_avatar_url(user.email, image_url, db)
    return user


@router.put(
    "/",
    description="No more than 3 requests per minute",
    dependencies=[Depends(RateLimiter(times=3, seconds=60))],
)
async def edit_my_name(
        name: str,
        user: User = Depends(auth_service.get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """
    Updates the name of the currently authenticated user.

    :param name: The new name of the user.
    :type name: str
    :param user: The currently authenticated user.
    :type user: User
    :param db: The async database session.
    :type db: AsyncSession
    :return: The updated user.
    :rtype: User
    """
    user = await repository_users.update_my_name(user, name, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NOT FOUND")
    return user


@router.get("/search/{search_query}", dependencies=[Depends(RateLimiter(times=1, seconds=10))],
            description="No more than 1 request per 10 seconds")
async def search_users(search_query: str = Path(..., min_length=1), db: AsyncSession = Depends(get_db),
                       current_user: User = Depends(auth_service.get_current_user)):
    """
    Searches for users by username or email. Available for all users.

    :param search_query: The query to search for
    :type search_query: str
    :param db: The async database session
    :type db: AsyncSession
    :param current_user: The currently authenticated user
    :type current_user: User
    :return: A list of users
    :rtype: List[User]
    """
    users_by_query = await repository_users.search_users(search_query, db)
    if len(users_by_query) == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Users with this query not found")
    return users_by_query
