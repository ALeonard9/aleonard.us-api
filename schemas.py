"""
This module defines the Pydantic models (schemas) for the API.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


# Data that comes from user
class UserBase(BaseModel):
    """
    Schema for user input data.
    """

    display_name: str
    email: str
    password: str


class UserDisplay(BaseModel):
    """
    Schema for displaying user data.
    """

    id: str
    display_name: str
    email: EmailStr
    user_group: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        from_attributes=True,
    )
