from typing import List
from pydantic import BaseModel, Field
from datetime import datetime


class ImageResponse(BaseModel):
    id: int
    link: str
    description: str
    user_id: int
    created_at: datetime

class ImageSchema(BaseModel):
    description: str = Field(max_length=250)
    tags: List[str] = Field(max_items=5)


class UpdateDescriptionSchema(BaseModel):
    description: str = Field(max_length=250)


class UpdateImageSchema(BaseModel):
    width: int = Field(le=1000)
    height: int = Field(le=1000)
