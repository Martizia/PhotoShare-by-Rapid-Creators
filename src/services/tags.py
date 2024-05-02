from fastapi import status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from src.database.models import Tag


async def get_or_create_tag(db: AsyncSession, tag_name: str) -> Tag:
    query = select(Tag).where(Tag.name == tag_name)
    result = await db.execute(query)
    tag = result.scalar_one_or_none()
    if not tag:
        tag = Tag(name=tag_name)
        db.add(tag)
        await db.commit()
    return tag


async def get_tags_list(db: AsyncSession, tags: List[str]) -> List[Tag]:
    new_tags_list = []
    for tag_name in tags:
        tag_names = tag_name.split(",")
        if len(tag_names) > 5:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Too many tags. Maximum allowed is 5.")
        for name in tag_names:
            tag = await get_or_create_tag(db, name.strip())
            new_tags_list.append(tag)
    return new_tags_list
