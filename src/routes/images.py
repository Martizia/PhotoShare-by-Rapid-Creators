from fastapi import APIRouter, Depends, UploadFile, File, status, HTTPException, Path
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession
import cloudinary.uploader
import random

from src.database.db import get_db
from src.database.models import User, Role, Effect, Crop, SortBy
from src.repository.images import create_image, delete_image_db, update_description_db, get_image_db, \
    save_transformed_image, generate_qrcode_by_image, get_transformed_image_db, search_images_by_description_or_tag, \
    sorter
from src.config.config import config
from src.schemas.images import ImageSchema, UpdateDescriptionSchema, UpdateImageSchema
from src.services.auth import auth_service
from src.services.roles import RoleAccess

cloudinary.config(
    cloud_name=config.CLOUDINARY_NAME,
    api_key=config.CLOUDINARY_API_KEY,
    api_secret=config.CLOUDINARY_API_SECRET,
    secure=True
)

router = APIRouter(
    prefix="/images",
    tags=["images"],
)
access_to_route_all = RoleAccess([Role.admin])


@router.post("/", status_code=status.HTTP_201_CREATED, dependencies=[Depends(RateLimiter(times=1, seconds=10))])
async def upload_image(file: UploadFile = File(...), body: ImageSchema = Depends(ImageSchema),
                       db: AsyncSession = Depends(get_db), current_user: User = Depends(auth_service.get_current_user)):
    """
    Uploads an image for the authenticated user.

    :param file: The image file to upload.
    :type file: UploadFile
    :param body: The data for the new image.
    :type body: ImageSchema
    :param db: The database session.
    :type db: AsyncSession
    :param current_user: The currently authenticated user.
    :type current_user: User
    :return: The newly created image.
    :rtype: Image
    """
    max_size = 5 * 1024 * 1024  # 5MB in bytes
    file_content = await file.read()
    file_size = len(file_content)
    if file_size > max_size:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File size exceeds 5MB")
    public_id = f'PhotoShare/{current_user.email}_{random.randint(1, 1000000)}'
    result = cloudinary.uploader.upload(file_content, public_id=public_id, overwrite=True)
    link = result['secure_url']
    return await create_image(db, link, body, current_user)


@router.delete("/{image_id}", status_code=status.HTTP_204_NO_CONTENT,
               dependencies=[Depends(RateLimiter(times=1, seconds=10))])
async def delete_image(image_id: int, db: AsyncSession = Depends(get_db),
                       current_user: User = Depends(auth_service.get_current_user)):
    """
    Deletes the image with the given ID for the authenticated user.

    :param image_id: The ID of the image to delete.
    :type image_id: int
    :param db: The database session.
    :type db: AsyncSession
    :param current_user: The currently authenticated user.
    :type current_user: User
    :return: A message indicating that the image was deleted.
    :rtype: dict
    """
    deleted = await delete_image_db(db, image_id, current_user)
    if deleted is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    return {"message": "Image deleted"}


@router.put("/{image_id}", dependencies=[Depends(RateLimiter(times=1, seconds=10))])
async def update_description(image_id: int, body: UpdateDescriptionSchema, db: AsyncSession = Depends(get_db),
                             current_user: User = Depends(auth_service.get_current_user)):
    """
    Updates the description of the image with the given ID for the authenticated user.

    :param image_id: The ID of the image to update.
    :type image_id: int
    :param body: The new description for the image.
    :type body: UpdateDescriptionSchema
    :param db: The database session.
    :type db: AsyncSession
    :param current_user: The currently authenticated user.
    :type current_user: User
    :return: The updated image.
    :rtype: Image
    """
    description = await update_description_db(db, image_id, body, current_user)
    if description is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    return description


@router.get("/{image_id}", dependencies=[Depends(RateLimiter(times=1, seconds=10))])
async def get_image(image_id: int, db: AsyncSession = Depends(get_db),
                    current_user: User = Depends(auth_service.get_current_user)):
    """
    Retrieves the image with the given ID for the authenticated user.

    :param image_id: The ID of the image to retrieve.
    :type image_id: int
    :param db: The async database session.
    :type db: AsyncSession
    :param current_user: The currently authenticated user.
    :type current_user: User
    :return: The retrieved image.
    :rtype: Image
    """
    image = await get_image_db(db, image_id, current_user)
    if image is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    return image


@router.post("/{image_id}/crop", dependencies=[Depends(RateLimiter(times=1, seconds=10))])
async def crop_image(image_id: int, size: UpdateImageSchema, crop: Crop, db: AsyncSession = Depends(get_db),
                     current_user: User = Depends(auth_service.get_current_user)):
    """
    Crops the image with the given ID for the authenticated user.

    :param image_id: The ID of the image to crop.
    :type image_id: int
    :param size: The new size of the image.
    :type size: UpdateImageSchema
    :param crop: The new crop of the image.
    :type crop: Crop
    :param db: The database session.
    :type db: AsyncSession
    :param current_user: The currently authenticated user.
    :type current_user: User
    :return: The cropped image.
    :rtype: Image
    """
    image = await get_image_db(db, image_id, current_user)
    if image is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")

    public_id = f'PhotoShare(transformed)/{current_user.email}_{random.randint(1, 1000000)}'
    transformed_image = cloudinary.uploader.upload(image.link, public_id=public_id,
                                                   transformation={"crop": f"{crop.value}", "width": f"{size.width}",
                                                                   "height": f"{size.height}"})
    link = transformed_image['secure_url']
    return await save_transformed_image(db, link, image_id)


@router.post("/{image_id}/effect", dependencies=[Depends(RateLimiter(times=1, seconds=10))])
async def use_effect(image_id: int, e: Effect, db: AsyncSession = Depends(get_db),
                     current_user: User = Depends(auth_service.get_current_user)):
    """
    Applies the effect to the image with the given ID for the authenticated user.

    :param image_id: The ID of the image to apply the effect to.
    :type image_id: int
    :param e: The effect to apply.
    :type e: Effect
    :param db: The database session.
    :type db: AsyncSession
    :param current_user: The currently authenticated user.
    :type current_user: User
    :return: The transformed image.
    :rtype: Image
    """
    image = await get_image_db(db, image_id, current_user)
    if image is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    public_id = f'PhotoShare(transformed)/{current_user.email}_{random.randint(1, 1000000)}'
    transformed_image = cloudinary.uploader.upload(image.link, public_id=public_id,
                                                   transformation={"effect": f"art:{e.value}"})
    link = transformed_image['secure_url']
    return await save_transformed_image(db, link, image_id)


@router.get("/{image_id}/qrcode", dependencies=[Depends(RateLimiter(times=1, seconds=10))])
async def generate_qrcode(image_id: int, db: AsyncSession = Depends(get_db),
                          current_user: User = Depends(auth_service.get_current_user)):
    """
    Generates a QR code for the image with the given ID for the authenticated user.

    :param image_id: The ID of the image to generate the QR code for.
    :type image_id: int
    :param db: The database session.
    :type db: AsyncSession
    :param current_user: The currently authenticated user.
    :type current_user: User
    :return: The generated QR code.
    :rtype: Image
    """
    image = await get_transformed_image_db(db, image_id)
    if image is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    return await generate_qrcode_by_image(image.link)


@router.get("/search/{image_query}", dependencies=[Depends(RateLimiter(times=1, seconds=10))])
async def search_images(order_by: SortBy, descending: bool, image_query: str = Path(..., min_length=2),
                        db: AsyncSession = Depends(get_db),
                        current_user: User = Depends(auth_service.get_current_user)):
    image_by_description = await search_images_by_description_or_tag(image_query, db)
    if len(image_by_description) == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Images with this query not found")
    sorted_images = await sorter(image_by_description, order_by, descending)
    return sorted_images
