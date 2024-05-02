from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.database.models import Image, User
from src.schemas.images import ImageSchema, UpdateImageSchema
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


async def update_description_db(db: AsyncSession, image_id: int, body: UpdateImageSchema, user: User) -> Image:
    query = select(Image).filter_by(id=image_id, user_id=user.id)
    result = await db.execute(query)
    image = result.scalar_one_or_none()
    if image:
        image.description = body.description
        # image.tags = []      # TODO якщо будемо додавати редагування усіх тегів
        # tags = await get_tags_list(db, body.tags)
        # for tag in tags:
        #     image.tags.append(tag)
        await db.commit()
        await db.refresh(image)
    return image


async def get_image_db(db: AsyncSession, image_id: int, user: User):
    query = select(Image).filter_by(id=image_id, user_id=user.id)
    result = await db.execute(query)
    return result.scalar_one_or_none().link
