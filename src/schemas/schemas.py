import re
from typing import Optional

from fastapi import HTTPException, status
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict

from src.schemas.users import UserResponse


class ContactModel(BaseModel):
    first_name: str = Field(max_length=15)
    last_name: str = Field(max_length=15)
    email: EmailStr
    contact_number: str
    additional_information: Optional[str] = None

    @field_validator('contact_number')  # noqa
    @classmethod
    def validate_contact_number(cls, value: str) -> str:
        if not re.match(r'^(\+\d{1,2}\s)?\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}$', value):
            """
            Matching formats:
            123-456-7890
            (123) 456-7890
            123 456 7890
            123.456.7890
            +12 (345) 678-9012
            """
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Invalid contact number")
        return value

class ContactResponse(ContactModel):
    id: int
    user: UserResponse | None
    model_config = ConfigDict(from_attributes=True)


class PasswordResetRequest(BaseModel):
    email: str


class PasswordReset(BaseModel):
    token: str
    new_password: str
