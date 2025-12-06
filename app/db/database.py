"""
This module sets up the database connection and session management.
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.log.logging_config import logger

ENV = os.getenv('ENV', 'local')
if ENV == 'local':
    SQLALCHEMY_DATABASE_URL = os.getenv(
        'DATABASE_URL', 'sqlite:///./aleonard-api-local.db'
    )
    logger.info('SQLALCHEMY_DATABASE_URL: %s', SQLALCHEMY_DATABASE_URL)
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={'check_same_thread': False}
    )
else:
    DB_USER = os.getenv('POSTGRES_USER')
    DB_PASSWORD = os.getenv('POSTGRES_PASSWORD')
    DB_HOST = os.getenv('POSTGRES_HOST')
    DB_PORT = os.getenv('POSTGRES_CONNECTION_PORT', '5432')
    DB_NAME = os.getenv('POSTGRES_DB', 'phoenix')
    SQLALCHEMY_DATABASE_URL = os.getenv(
        'DATABASE_URL',
        f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}",
    )
    logger.info('SQLALCHEMY_DATABASE_URL: %s', DB_HOST)
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine
)  # pylint: disable=invalid-name
Base = declarative_base()


def get_db():
    """
    Dependency that provides a SQLAlchemy session to be used in route handlers.

    Yields:
        Session: A SQLAlchemy session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
