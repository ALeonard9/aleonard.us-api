"""
This module contains tests for the database module.
"""

import pytest
from sqlalchemy.orm import Session

from db.database import get_db


def test_get_db():
    """
    Test that get_db yields a SQLAlchemy session.
    """
    db_generator = get_db()
    try:
        db = next(db_generator)
        assert isinstance(db, Session), 'get_db should yield a Session instance'
    except StopIteration:
        pytest.fail('get_db should yield a Session instance')
    # Ensure subsequent next call raises StopIteration
    with pytest.raises(StopIteration):
        next(db_generator)
