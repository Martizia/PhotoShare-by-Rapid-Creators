from fastapi import APIRouter, Depends, UploadFile, File, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import cloudinary.uploader
import random

from src.database.db import get_db
from src.database.models import User, Role
from src.repository.images import create_image, delete_image_db, update_description_db, get_image_db
from src.config.config import config
from src.schemas.images import ImageSchema, UpdateImageSchema
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


@router.post("/", status_code=status.HTTP_201_CREATED)
async def upload_image(file: UploadFile = File(...), body: ImageSchema = Depends(ImageSchema),
                       db: AsyncSession = Depends(get_db), current_user: User = Depends(auth_service.get_current_user)):
    public_id = f'PhotoShare/{current_user.email}_{random.randint(1, 1000000)}'
    result = cloudinary.uploader.upload(file.file, public_id=public_id, overwrite=True)
    link = result['secure_url']
    return await create_image(db, link, body, current_user)


@router.delete("/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_image_route(image_id: int, db: AsyncSession = Depends(get_db),
                             current_user: User = Depends(auth_service.get_current_user)):
    deleted = await delete_image_db(db, image_id, current_user)
    return deleted


@router.put("/{image_id}")
async def update_description(image_id: int, body: UpdateImageSchema, db: AsyncSession = Depends(get_db),
                             current_user: User = Depends(auth_service.get_current_user)):
    description = await update_description_db(db, image_id, body, current_user)
    if description is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Image not found")
    return description


@router.get("/{image_id}")
async def get_image(image_id: int, db: AsyncSession = Depends(get_db),
                    current_user: User = Depends(auth_service.get_current_user)):
    image = await get_image_db(db, image_id, current_user)
    if image is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return image
