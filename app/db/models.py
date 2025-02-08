"""
This module defines the database models.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String

from app.db.database import Base


class DBBaseModel(Base):
    """
    Base model that includes common fields for all tables.
    """

    __abstract__ = True  # This class won't be created as a table in the database
    # Primary key never shared externally/ only used for relationships and indexing
    pk = Column(Integer, primary_key=True, index=True, autoincrement=True)
    # Ok to include in API responses
    id = Column(String, default=lambda: str(uuid.uuid4()), index=True, unique=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class DbUser(DBBaseModel):
    """
    Database model for users.
    """

    __tablename__ = 'users'
    email = Column(String, unique=True)
    display_name = Column(String(length=30))
    user_group = Column(String, default='user')
    password = Column(String)
