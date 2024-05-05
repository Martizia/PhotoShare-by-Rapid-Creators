from io import BytesIO

import qrcode
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from starlette.responses import StreamingResponse

from src.database.models import Image, User, TransformedImage
from src.schemas.images import ImageSchema, UpdateDescriptionSchema
from src.services.tags import get_tags_list


async def create_image(db: AsyncSession, link: str, body: ImageSchema, user: User) -> Image:
    image = Image(link=link, description=body.description, user_id=user.id)
    tags = await get_tags_list(db, body.tags)
    for tag in tags:
        image.tags.append(tag)
    db.add(image)
    await db.commit()
    await db.refresh(image)
    return image


async def delete_image_db(db: AsyncSession, image_id: int, user: User) -> Image:
    query = select(Image).filter_by(id=image_id, user_id=user.id)
    result = await db.execute(query)
    image = result.scalar_one_or_none()
    if image:
        await db.delete(image)
        await db.commit()
    return image


async def update_description_db(db: AsyncSession, image_id: int, body: UpdateDescriptionSchema, user: User) -> Image:
    query = select(Image).filter_by(id=image_id, user_id=user.id)
    result = await db.execute(query)
    image = result.scalar_one_or_none()
    if image:
        image.description = body.description
        await db.commit()
        await db.refresh(image)
    return image


async def get_image_db(db: AsyncSession, image_id: int, user: User):
    query = select(Image).filter_by(id=image_id, user_id=user.id)
    result = await db.execute(query)
    result_one = result.scalar_one_or_none()
    return result_one


async def save_transformed_image(db: AsyncSession, link: str, image_id: int):
    image = TransformedImage(link=link, image_id=image_id)
    db.add(image)
    await db.commit()
    await db.refresh(image)
    return image


async def generate_qrcode_by_image(image: str):
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(image)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    buffer = BytesIO()
    img.save(buffer, "PNG")
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="image/png")


async def get_transformed_image_db(db: AsyncSession, image_id: int):
    query = select(TransformedImage).filter_by(id=image_id)
    result = await db.execute(query)
    result_one = result.scalar_one_or_none()
    return result_one


async def search_images_by_query(db: AsyncSession, query: str):
    query = select(Image).filter(Image.description.ilike(f"%{query}%"))
    result = await db.execute(query)
    result = result.scalars().all()
    return result
