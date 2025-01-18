"""
This module contains unit tests for the DbUser model.
"""

import pytest

from db.models import DbUser


@pytest.mark.parametrize(
    'email,display_name,user_group',
    [
        ('test@example.com', 'Test User', 'user'),
        ('admin@example.com', 'Admin User', 'admin'),
    ],
)
def test_create_db_user_defaults(email, display_name, user_group):
    """
    Test creating a DbUser with default values.
    """
    user = DbUser(email=email, display_name=display_name, user_group=user_group)
    assert user.email == email
    assert user.display_name == display_name
    assert user.user_group == user_group
    assert user.pk is None  # Primary key not set until saved in DB
