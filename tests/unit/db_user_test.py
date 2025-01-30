'''
This file contains unit tests for the db_user module.
'''

import os
import uuid
from datetime import datetime
from typing import Any, Dict, List
from unittest.mock import patch

import pytest
from faker import Faker
from fastapi import HTTPException, status

from db.db_user import (
    create_admin_user,
    create_user,
    get_all_users,
    get_user,
    update_user,
)
from db.hash import Hash
from db.models import DbUser
from schemas import InUserBase

fake = Faker()


def assert_user_fields(
    users: List[DbUser], expected_data: List[Dict[str, Any]], admin=False
):
    '''
    Helper function that takes a list of users and expected data and asserts that the fields match.
    '''
    for i, user in enumerate(users):
        assert (
            user.display_name == expected_data[i].display_name
        ), 'display_name should match submission'
        assert user.email == expected_data[i].email, 'email should match submission'
        assert isinstance(user.pk, int), 'pk should be an integer'
        assert user.id is not None, 'id should not be None'
        assert uuid.UUID(user.id), f'{user.id} is not a valid UUID'
        assert Hash.verify(user.password, expected_data[i].password)
        assert user.user_group == (
            'admin' if admin else 'user'
        ), f'user_group should be {"admin" if admin else "user"}'
        assert user.created_at is not None, 'created_at should not be None'
        assert user.updated_at is not None, 'updated_at should not be None'
        assert isinstance(
            user.created_at, datetime
        ), 'created_at should be a datetime object'
        assert isinstance(
            user.updated_at, datetime
        ), 'updated_at should be a datetime object'


def test_create_user(test_db_session, test_user_data_generator):
    '''
    Test creating a new user in the database.
    '''
    user_data_list = test_user_data_generator(num_users=1)
    test_user_data = user_data_list[0]
    new_user = create_user(test_db_session, test_user_data)
    assert isinstance(new_user, list)
    assert_user_fields(new_user, user_data_list)


def test_create_multiple_users(test_db_session, test_user_data_generator):
    '''
    Test creating multiple users in the database.
    '''
    user_data_list = test_user_data_generator(num_users=3)
    for test_user_data in user_data_list:

        new_user = create_user(test_db_session, test_user_data)
        assert isinstance(new_user, list)
        expected_data = [test_user_data]
        assert_user_fields(new_user, expected_data)


def test_create_user_existing_email(test_db_session, test_user_data_generator):
    '''
    Test creating a user with an existing email raises an HTTPException.
    '''
    user_data_list = test_user_data_generator(num_users=1)
    test_user_data = user_data_list[0]
    create_user(test_db_session, test_user_data)
    with pytest.raises(HTTPException) as exc_info:
        create_user(test_db_session, test_user_data)
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert exc_info.value.detail == 'Email already registered'


def test_create_user_invalid_email(test_db_session, test_user_data_generator):
    '''
    Test creating a user with an invalid email raises an HTTPException.
    '''
    user_data_list = test_user_data_generator(num_users=1)
    test_user_data = user_data_list[0]
    test_user_data.email = 'invalidemail'
    with pytest.raises(HTTPException) as exc_info:
        create_user(test_db_session, test_user_data)
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert exc_info.value.detail == 'Invalid email address'


def test_create_admin_user(test_db_session, test_user_data_generator):
    '''
    Test creating an admin user in the database.
    '''
    user_data_list = test_user_data_generator(num_users=1)
    test_user_data = user_data_list[0]
    with patch.dict(
        os.environ,
        {
            'ADMIN_DISPLAY_NAME': test_user_data.display_name,
            'ADMIN_EMAIL': test_user_data.email,
            'ADMIN_PASSWORD': test_user_data.password,
        },
    ):
        admin_user = create_admin_user(test_db_session)
    assert isinstance(admin_user, list)
    assert_user_fields(admin_user, user_data_list, admin=True)


def test_create_admin_user_no_env_vars(test_db_session, monkeypatch):
    '''
    Test creating an admin user with missing environment variables raises an HTTPException.
    '''
    monkeypatch.delenv('ADMIN_DISPLAY_NAME', raising=False)
    monkeypatch.delenv('ADMIN_EMAIL', raising=False)
    monkeypatch.delenv('ADMIN_PASSWORD', raising=False)
    with pytest.raises(HTTPException) as exc_info:
        create_admin_user(test_db_session)
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert exc_info.value.detail == 'Environment variables not set for admin creation'


def test_create_admin_existing_email(test_db_session, test_user_data_generator):
    '''
    Test creating a user with an existing email raises an HTTPException.
    '''
    user_data_list = test_user_data_generator(num_users=1)
    test_user_data = user_data_list[0]
    with patch.dict(
        os.environ,
        {
            'ADMIN_DISPLAY_NAME': test_user_data.display_name,
            'ADMIN_EMAIL': test_user_data.email,
            'ADMIN_PASSWORD': test_user_data.password,
        },
    ):
        create_admin_user(test_db_session)
    with pytest.raises(HTTPException) as exc_info:
        with patch.dict(
            os.environ,
            {
                'ADMIN_DISPLAY_NAME': test_user_data.display_name,
                'ADMIN_EMAIL': test_user_data.email,
                'ADMIN_PASSWORD': test_user_data.password,
            },
        ):
            create_admin_user(test_db_session)
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert exc_info.value.detail == 'Email already registered'


def test_create_admin_invalid_email(test_db_session, test_user_data_generator):
    '''
    Test creating a user with an invalid email raises an HTTPException.
    '''
    user_data_list = test_user_data_generator(num_users=1)
    test_user_data = user_data_list[0]
    test_user_data.email = 'invalidemail'
    with pytest.raises(HTTPException) as exc_info:
        with patch.dict(
            os.environ,
            {
                'ADMIN_DISPLAY_NAME': test_user_data.display_name,
                'ADMIN_EMAIL': test_user_data.email,
                'ADMIN_PASSWORD': test_user_data.password,
            },
        ):
            create_admin_user(test_db_session)
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert exc_info.value.detail == 'Invalid email address'


def test_get_all_users(test_db_session, test_user_data_generator):
    '''
    Test getting all users from the database.
    '''
    iterations = 3
    user_data_list = test_user_data_generator(num_users=iterations)
    for user_data in user_data_list:
        create_user(test_db_session, user_data)
    users = get_all_users(test_db_session)
    assert isinstance(users, list)
    assert len(users) == iterations
    assert_user_fields(users, user_data_list)


def test_get_all_users_no_users(test_db_session):
    '''
    Test getting all users from the database when there are no users.
    '''
    users = get_all_users(test_db_session)
    assert isinstance(users, list)
    assert users == []


def test_get_user(test_db_session, test_user_data_generator):
    '''
    Test getting a user from the database.
    '''
    user_data_list = test_user_data_generator(num_users=1)
    test_user_data = user_data_list[0]
    new_user = create_user(test_db_session, test_user_data)
    user_retrieved = get_user(test_db_session, new_user[0].id)
    assert isinstance(user_retrieved, list)
    assert_user_fields(user_retrieved, user_data_list)


def test_get_user_not_found(test_db_session):
    '''
    Test getting a user from the database that does not exist raises an HTTPException.
    '''
    fake_uuid = fake.uuid4()
    with pytest.raises(HTTPException) as exc_info:
        get_user(test_db_session, fake_uuid)
    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    assert exc_info.value.detail == f'User with id {fake_uuid} not found'


def test_update_user(test_db_session, test_user_data_generator):
    '''
    Test updating a user in the database.
    '''
    user_data_list = test_user_data_generator(num_users=2)
    test_user_data = user_data_list[0]
    test_second_user_data = user_data_list[1]
    new_user = create_user(test_db_session, test_user_data)
    new_display_name = test_second_user_data.display_name
    new_email = test_second_user_data.email
    new_password = test_second_user_data.password
    new_user_data = InUserBase(
        display_name=new_display_name, email=new_email, password=new_password
    )
    updated_user = update_user(test_db_session, new_user[0].id, new_user_data)
    assert isinstance(updated_user, list)
    expected_data = [test_second_user_data]
    assert_user_fields(updated_user, expected_data)


def test_update_user_not_found(test_db_session, test_user_data_generator):
    '''
    Test updating a user in the database that does not exist raises an HTTPException.
    '''
    user_data_list = test_user_data_generator(num_users=1)
    test_user_data = user_data_list[0]
    fake_uuid = fake.uuid4()
    with pytest.raises(HTTPException) as exc_info:
        update_user(test_db_session, fake_uuid, test_user_data)
    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    assert exc_info.value.detail == f'User with id {fake_uuid} not found'


def test_update_user_invalid_email(test_db_session, test_user_data_generator):
    '''
    Test updating a user in the database with an invalid email raises an HTTPException.
    '''
    user_data_list = test_user_data_generator(num_users=1)
    test_user_data = user_data_list[0]
    new_user = create_user(test_db_session, test_user_data)
    test_user_data.email = 'invalidemail'
    with pytest.raises(HTTPException) as exc_info:
        update_user(test_db_session, new_user[0].id, test_user_data)
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert exc_info.value.detail == 'Invalid email address'


def test_update_user_existing_email(test_db_session, test_user_data_generator):
    '''
    Test updating a user in the database with an existing email raises an HTTPException.
    '''
    user_data_list = test_user_data_generator(num_users=2)
    test_user_data = user_data_list[0]
    test_second_user_data = user_data_list[1]
    new_user = create_user(test_db_session, test_user_data)
    create_user(test_db_session, test_second_user_data)
    test_user_data.email = test_second_user_data.email
    with pytest.raises(HTTPException) as exc_info:
        update_user(test_db_session, new_user[0].id, test_user_data)
    assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
    assert exc_info.value.detail == 'Email already registered'


def test_delete_user(test_db_session, test_user_data_generator):
    '''
    Test deleting a user from the database.
    '''
    user_data_list = test_user_data_generator(num_users=1)
    test_user_data = user_data_list[0]
    new_user = create_user(test_db_session, test_user_data)
    db_user = get_user(test_db_session, new_user[0].id)
    test_db_session.delete(db_user[0])
    test_db_session.commit()
    with pytest.raises(HTTPException) as exc_info:
        get_user(test_db_session, new_user[0].id)
    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    assert exc_info.value.detail == f'User with id {new_user[0].id} not found'


def test_delete_user_not_found(test_db_session):
    '''
    Test deleting a user from the database that does not exist raises an HTTPException.
    '''
    fake_uuid = fake.uuid4()
    with pytest.raises(HTTPException) as exc_info:
        db_user = get_user(test_db_session, fake_uuid)
        test_db_session.delete(db_user)  # pragma: no cover
        test_db_session.commit()  # pragma: no cover
    assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
    assert exc_info.value.detail == f'User with id {fake_uuid} not found'
