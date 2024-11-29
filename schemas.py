"""
This module defines the Pydantic models (schemas) for the API.
"""

from datetime import datetime
from pydantic import BaseModel


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
    email: str
    user_group: str
    created_at: datetime
    updated_at: datetime

    class Config:
        """
        Configuration for the Pydantic model.
        """

        from_attributes = True
