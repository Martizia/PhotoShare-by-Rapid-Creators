from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field




class CommentModel(BaseModel):
    text: str = Field(max_length=250)
    image_id: int