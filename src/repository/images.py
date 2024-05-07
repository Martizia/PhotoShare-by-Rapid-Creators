from io import BytesIO

import qrcode
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import aliased
from sqlalchemy.sql.expression import or_
from starlette.responses import StreamingResponse
from operator import attrgetter

from src.database.models import Image, User, TransformedImage, Tag, SortBy, Rating
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
    """
    Searches images by description or tag and includes the average rating for each image.

    :param search_string: The string to search for.
    :type search_string: str
    :param db: The async database session.
    :type db: AsyncSession
    :return: The list of images that match the search string with their average ratings.
    :rtype: list[dict]
    """
    ImageAlias = aliased(Image)
    average_rating_subquery = select(
        Rating.image_id,
        func.avg(Rating.rating).label("average_rating")
    ).group_by(
        Rating.image_id
    ).subquery()
    query = select(
        ImageAlias,
        average_rating_subquery.c.average_rating
    ).join(
        ImageAlias.tags
    ).join(
        average_rating_subquery,
        ImageAlias.id == average_rating_subquery.c.image_id
    ).where(
        or_(
            ImageAlias.description.ilike(f"%{search_string}%"),
            Tag.name.ilike(f"%{search_string}%")
        )
    ).distinct()
    result = await db.execute(query)
    images_with_ratings = result.all()
    response = []
    for image, average_rating in images_with_ratings:
        response.append({
            "link": image.link,
            "id": image.id,
            "user_id": image.user_id,
            "description": image.description,
            "created_at": image.created_at,
            "average_rating": average_rating
        })

    return response


async def sorter(images: list, order_by: SortBy, descending: bool):
    """
    Sorts images by rating or date.

    :param images: The list of images to sort.
    :type images: list
    :param order_by: The order to sort by.
    :type order_by: SortBy
    :param descending: Whether to sort in descending order.
    :type descending: bool
    :return: The sorted list of images.
    :rtype: list
    """
    if order_by == SortBy.rating:
        images.sort(key=lambda x: x.get('average_rating', 0), reverse=descending)
    elif order_by == SortBy.date:
        images.sort(key=lambda x: x.get('created_at'), reverse=descending)
    return images


async def get_images_by_user_id(db: AsyncSession, user_id: int):
    """
    Gets images by user id.

    :param db: The async database session.
    :type db: AsyncSession
    :param user_id: The ID of the user.
    :type user_id: int
    :return: The list of images for the user.
    :rtype: list[Image]
    """
    query = select(Image).filter_by(user_id=user_id)
    result = await db.execute(query)
    return result.scalars().all()
