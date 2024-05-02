from typing import List
from pydantic import BaseModel, Field


class ImageSchema(BaseModel):
    description: str = Field(max_length=250)
    tags: List[str] = Field(max_items=5)


class UpdateImageSchema(BaseModel):
    description: str = Field(max_length=250)
