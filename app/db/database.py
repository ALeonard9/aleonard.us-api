"""
This module sets up the database connection and session management.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import get_settings
from app.log.logging_config import logger

settings = get_settings()
SQLALCHEMY_DATABASE_URL = settings.sqlalchemy_database_url

if settings.is_local:
    logger.info('SQLALCHEMY_DATABASE_URL: %s', SQLALCHEMY_DATABASE_URL)
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={'check_same_thread': False}
    )
else:
    logger.info('SQLALCHEMY_DATABASE_URL host: %s', settings.postgres_host)
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
