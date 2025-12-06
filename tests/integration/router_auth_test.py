"""
Tests the user API calls
"""

from faker import Faker
from fastapi.testclient import TestClient

fake = Faker()


def test_api_user_get_token(
    test_client: TestClient,
):
    """
    Test creating a new user.
    """
    email = test_client.first_user.email
    password = test_client.first_user.plain_password
    response = test_client.post(
        '/v1/auth/token',
        files={
            'username': (None, email),
            'password': (None, password),
        },
    )
    assert response.status_code == 200
    response_data = response.json()
    assert response_data['access_token']
    assert response_data['token_type'] == 'bearer'
    assert response_data['user_id'] == test_client.first_user.id
    assert response_data['email'] == test_client.first_user.email
    assert response_data['user_group'] == 'user'


def test_api_user_token_bad_password(
    test_client: TestClient,
):
    """
    Test token creation with bad password.
    """
    email = test_client.first_user.email
    password = fake.password(length=20)
    response = test_client.post(
        '/v1/auth/token',
        files={
            'username': (None, email),
            'password': (None, password),
        },
    )
    assert response.status_code == 404
    response_data = response.json()
    assert response_data['success'] is False
    assert response_data['message'] == 'Invalid credentials'
    assert response_data['data'] == []


def test_api_user_token_bad_user(
    test_client: TestClient,
):
    """
    Test token creation with bad password.
    """
    email = fake.email()
    password = test_client.first_user.plain_password
    response = test_client.post(
        '/v1/auth/token',
        files={
            'username': (None, email),
            'password': (None, password),
        },
    )
    assert response.status_code == 404
    response_data = response.json()
    assert response_data['success'] is False
    assert response_data['message'] == 'Invalid credentials'
    assert response_data['data'] == []
