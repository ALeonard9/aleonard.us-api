"""
This module defines the database models.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

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

    # --- Visibility (#143): everything is private by default. A public
    # profile needs a handle (druthers.io/u/<handle>) plus at least one
    # category switched on; only ranked lists are ever exposed.
    handle = Column(String(length=30), unique=True, index=True, nullable=True)
    public_movies = Column(Boolean, nullable=True, default=False)
    public_tv = Column(Boolean, nullable=True, default=False)
    public_books = Column(Boolean, nullable=True, default=False)
    public_games = Column(Boolean, nullable=True, default=False)


class DbApiKey(DBBaseModel):
    """
    Long-lived API key for programmatic access (MCP servers, crons).

    Only the SHA-256 hash of the secret is stored; the plaintext is shown
    exactly once at creation. ``prefix`` is a short display hint so a user
    can tell keys apart in a list.
    """

    __tablename__ = 'api_keys'
    user_id = Column(Integer, ForeignKey('users.pk'), nullable=False)
    name = Column(String(length=60), nullable=False)
    key_hash = Column(String(length=64), unique=True, index=True, nullable=False)
    prefix = Column(String(length=12), nullable=False)
    last_used_at = Column(DateTime, nullable=True)

    user = relationship('DbUser', backref='api_keys')


# Import sandbox models to ensure they are registered with the Base metadata
# pylint: disable=cyclic-import, wrong-import-position, unused-import
from app.db import models_sandbox  # noqa: F401
