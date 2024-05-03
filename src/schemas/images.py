from typing import List, Literal
from pydantic import BaseModel, Field


class ImageSchema(BaseModel):
    description: str = Field(max_length=250)
    tags: List[str] = Field(max_items=5)


class UpdateDescriptionSchema(BaseModel):
    description: str = Field(max_length=250)


class UpdateImageSchema(BaseModel):
    width: int = Field(le=1000)
    height: int = Field(le=600)
    crop: Literal['crop', 'scale', 'fill'] = Field(description="Choose one of the options: crop, scale, fill")


class EffectSchema(BaseModel):
    effect: Literal[
        'al_dente', 'athena', 'audrey', 'aurora', 'daguerre', "eucalyptus", 'fes', "frost", 'hairspray', 'hokusai',
        'incognito', 'linen', 'peacock', 'primavera', 'quartz', 'red_rock', 'refresh', 'sizzle', 'sonnet', 'ukulele',
        'zorro'] = Field(
        description="Choose one of the options: al_dente, athena, audrey, aurora, daguerre, eucalyptus, fes, frost, "
                    "hairspray, hokusai, incognito, linen, peacock, primavera, quartz, red_rock, refresh, sizzle, "
                    "sonnet, ukulele, zorro")
