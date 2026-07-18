"""
This module defines the Pydantic models (schemas) for the API.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# User data provided as input
class InUserBase(BaseModel):
    """
    Schema for user input data.
    """

    display_name: str
    email: str
    password: str


# User data returned in a response
class OutUserDisplay(BaseModel):
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


class OutResponseBaseModel(BaseModel):
    """
    All responses will have this format.
    """

    success: bool = True
    data: Optional[list] = []
    message: Optional[str] = 'None'

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        from_attributes=True,
        # These appear not to work. Ideally we would exclude None and unset.
        exclude_none=True,
        exclude_unset=True,
    )


class OutResponseUserModel(OutResponseBaseModel):
    """
    Response format for user data.
    """

    data: list[OutUserDisplay]

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        from_attributes=True,
    )


class InApiKeyCreate(BaseModel):
    """
    Request body for minting an API key.
    """

    name: str = Field(min_length=1, max_length=60)


class OutApiKey(BaseModel):
    """
    An API key as shown in listings — never includes the secret.
    """

    id: str
    name: str
    prefix: str
    created_at: datetime
    last_used_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class OutApiKeyCreated(OutApiKey):
    """
    Creation response: the one and only time the plaintext key appears.
    """

    key: str
