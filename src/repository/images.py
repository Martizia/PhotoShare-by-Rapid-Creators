from io import BytesIO

import qrcode
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.sql.expression import or_
from starlette.responses import StreamingResponse
from operator import attrgetter

from src.database.models import Image, User, TransformedImage, Tag, SortBy
from src.schemas.images import ImageSchema, UpdateDescriptionSchema
from src.services.tags import get_tags_list


async def create_image(db: AsyncSession, link: str, body: ImageSchema, user: User) -> Image:
    """
    Creates an image owned by current user.

    :param db: The async database session.
    :type db: AsyncSession
    :param link: Link to image
    :type link: str
    :param body: The data for the image to create.
    :type body: ImageSchema
    :param user: Current user that creates the image
    :type user: User
    :return: The newly created image.
    :rtype: Image
    """
    image = Image(link=link, description=body.description, user_id=user.id)
    tags = await get_tags_list(db, body.tags)
    for tag in tags:
        image.tags.append(tag)
    db.add(image)
    await db.commit()
    await db.refresh(image)
    return image


async def delete_image_db(db: AsyncSession, image_id: int, user: User) -> Image:
    """
    Deletes an image owned by current user.

    :param db: The async database session.
    :type db: AsyncSession
    :param image_id: The ID of the image to delete.
    :type image_id: int
    :param user: Current user that deletes the image
    :type user: User
    :return: The deleted image, or None if it does not exist.
    :rtype: Image | None
    """
    query = select(Image).filter_by(id=image_id, user_id=user.id)
    result = await db.execute(query)
    image = result.scalar_one_or_none()
    if image:
        await db.delete(image)
        await db.commit()
    return image


async def update_description_db(db: AsyncSession, image_id: int, body: UpdateDescriptionSchema, user: User) -> Image:
    """
    Updates an image owned by current user.

    :param db: The async database session.
    :type db: AsyncSession
    :param image_id: The ID of the image to update.
    :type image_id: int
    :param body: The updated data for the image.
    :type body: UpdateDescriptionSchema
    :param user: Current user that updates the image
    :type user: User
    :return: The updated image, or None if it does not exist.
    :rtype: Image | None
    """
    query = select(Image).filter_by(id=image_id, user_id=user.id)
    result = await db.execute(query)
    image = result.scalar_one_or_none()
    if image:
        image.description = body.description
        await db.commit()
        await db.refresh(image)
    return image


async def get_image_db(db: AsyncSession, image_id: int, user: User):
    """
    Gets an image owned by current user.

    :param db: The async database session.
    :type db: AsyncSession
    :param image_id: The ID of the image to get.
    :type image_id: int
    :param user: Current user that gets the image
    :type user: User
    :return: The image, or None if it does not exist.
    :rtype: Image | None
    """
    query = select(Image).filter_by(id=image_id, user_id=user.id)
    result = await db.execute(query)
    result_one = result.scalar_one_or_none()
    return result_one


async def save_transformed_image(db: AsyncSession, link: str, image_id: int):
    """
    Saves transformed image.

    :param db: The async database session.
    :type db: AsyncSession
    :param link: Link to image
    :type link: str
    :param image_id: ID of image
    :type image_id: int
    :return: Transformed image
    :rtype: TransformedImage
    """
    image = TransformedImage(link=link, image_id=image_id)
    db.add(image)
    await db.commit()
    await db.refresh(image)
    return image


async def generate_qrcode_by_image(image: str):
    """
    Generates qrcode by image.

    :param image: Link to image
    :type image: str
    :return: Transformed image
    :rtype: TransformedImage
    """
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(image)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    buffer = BytesIO()
    img.save(buffer, "PNG")
    buffer.seek(0)
    return StreamingResponse(buffer, media_type="image/png")


async def get_transformed_image_db(db: AsyncSession, image_id: int):
    """
    Gets transformed image.

    :param db: The async database session.
    :type db: AsyncSession
    :param image_id: The ID of the image to get.
    :type image_id: int
    :return: The transformed image, or None if it does not exist.
    :rtype: TransformedImage | None
    """
    query = select(TransformedImage).filter_by(id=image_id)
    result = await db.execute(query)
    result_one = result.scalar_one_or_none()
    return result_one


async def search_images_by_description_or_tag(search_string: str, db: AsyncSession):
    query = select(Image).join(Image.tags).filter(
        or_(Image.description.ilike(f"%{search_string}%"), Tag.name.ilike(f"%{search_string}%"))).distinct()
    result = await db.execute(query)
    return result.scalars().all()


async def sorter(images: list, order_by: SortBy, descending: bool):
    if order_by.value == 'rating':
        images.sort(key=lambda x: getattr(x, 'average_rating', 0), reverse=descending)  #не працює
    elif order_by.value == 'date':
        images.sort(key=attrgetter('created_at'), reverse=descending)
    return images
