"""
This module contains unit tests for the OutResponseUserModel.
"""

from datetime import datetime, timezone

from faker import Faker

from schemas import OutResponseUserModel, OutUserDisplay

fake = Faker()


def test_out_response_user_model_with_all_fields(test_user_data_generator):
    """
    Test OutResponseUserModel with all fields provided.
    """
    user_data_list = test_user_data_generator(num_users=1)
    user = OutUserDisplay(
        id=fake.uuid4(),
        display_name=user_data_list[0].display_name,
        email=user_data_list[0].email,
        user_group='admin',
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    response = OutResponseUserModel(
        success=True, data=[user], message='Users retrieved successfully.'
    )

    assert response.success is True
    assert len(response.data) == 1
    assert response.data[0].display_name == user_data_list[0].display_name
    assert response.data[0].email == user_data_list[0].email
    assert response.data[0].user_group == 'admin'
    assert response.message == 'Users retrieved successfully.'


def test_out_response_user_model_without_message(test_user_data_generator):
    """
    Test OutResponseUserModel without providing the 'message' field.
    """
    user_data_list = test_user_data_generator(num_users=1)
    user = OutUserDisplay(
        id=fake.uuid4(),
        display_name=user_data_list[0].display_name,
        email=user_data_list[0].email,
        user_group='user',
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )

    response = OutResponseUserModel(success=True, data=[user])

    assert response.success is True
    assert len(response.data) == 1
    assert response.data[0].email == user_data_list[0].email
    assert response.message == 'None'


def test_out_response_user_model_without_success():
    """
    Test OutResponseUserModel without providing the 'success' field.
    """
    response = OutResponseUserModel(data=[], message='Users retrieved successfully.')

    assert response.success is True
    assert not response.data
    assert response.message == 'Users retrieved successfully.'
