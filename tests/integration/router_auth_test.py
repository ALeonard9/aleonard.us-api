"""
Tests the user API calls
"""

from unittest.mock import patch

from faker import Faker
from fastapi.testclient import TestClient

from app.config import Settings

fake = Faker()


@patch('app.auth.authentication.get_settings')
@patch('app.auth.authentication.google_id_token.verify_oauth2_token')
def test_google_login_creates_user(mock_verify, mock_settings, test_client: TestClient):
    """A valid Google credential signs in and creates the user on first use."""
    mock_settings.return_value = Settings(google_client_id='client-123', env='github')
    email = f'{fake.user_name()}@gmail.com'
    mock_verify.return_value = {
        'email': email,
        'email_verified': True,
        'name': 'Test Google User',
    }
    response = test_client.post(
        '/v1/auth/google', json={'credential': 'fake-google-id-token'}
    )
    assert response.status_code == 200
    data = response.json()
    assert data['access_token']
    assert data['email'] == email
    assert data['user_group'] == 'user'


@patch('app.auth.authentication.get_settings')
@patch('app.auth.authentication.google_id_token.verify_oauth2_token')
def test_google_login_rejects_invalid_token(
    mock_verify, mock_settings, test_client: TestClient
):
    """An invalid Google credential is rejected with 401."""
    mock_settings.return_value = Settings(google_client_id='client-123', env='github')
    mock_verify.side_effect = ValueError('bad token')
    response = test_client.post('/v1/auth/google', json={'credential': 'bad'})
    assert response.status_code == 401


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
