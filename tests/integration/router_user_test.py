"""
Tests the user API calls
"""

from typing import Callable

from fastapi.testclient import TestClient


def authenticate_user(auth_client: TestClient, email: str, password: str) -> str:
    """
    Authenticate a user and return the access token.
    """
    response = auth_client.post(
        '/v1/auth/token/', json={'username': email, 'password': password}
    )
    print(response.json())

    assert response.status_code == 200, 'Authentication failed'
    token = response.json().get('access_token')
    return token


def test_api_create_user(
    client: TestClient, test_user_data_generator: Callable[..., list]
):
    """
    Test creating a new user.
    """
    user_data_list = test_user_data_generator(num_users=1)
    test_user_data = user_data_list[0]
    user_data = {
        'display_name': test_user_data.display_name,
        'email': test_user_data.email,
        'password': test_user_data.password,
    }
    print('user_data:', user_data)
    response = client.post('/v1/users/', json=user_data)

    print(response.json())
    assert response.status_code == 201
    response_data = response.json()
    assert response_data['success'] is True
    assert response_data['message'] == 'User created'
    assert response_data['data'][0]['email'] == test_user_data.email
    assert response_data['data'][0]['display_name'] == test_user_data.display_name


def test_api_get_user(
    client: TestClient, test_user_data_generator: Callable[..., list]
):
    """
    Test getting a user.
    """
    user_data_list = test_user_data_generator(num_users=1)
    test_user_data = user_data_list[0]
    user_data = {
        'display_name': test_user_data.display_name,
        'email': test_user_data.email,
        'password': test_user_data.password,
    }
    post_response = client.post('/v1/users/', json=user_data)
    assert post_response.status_code == 201
    post_response_data = post_response.json()
    user_id = post_response_data['data'][0]['id']

    auth_response = client.post(
        '/v1/auth/token/',
        files={
            'username': (None, test_user_data.email),
            'password': (None, test_user_data.password),
        },
    )
    print(auth_response.json())

    assert auth_response.status_code == 200, 'Authentication failed'
    token = auth_response.json().get('access_token')
    # token = authenticate_user(client, test_user_data.email, test_user_data.password)
    assert token is not None

    headers = {'Authorization': f"Bearer {token}"}
    get_response = client.get(f"/v1/users/{user_id}", headers=headers)

    assert get_response.status_code == 200
    response_data = get_response.json()
    assert response_data['success'] is True
    assert response_data['message'] == 'User found'
    assert response_data['data'][0]['email'] == test_user_data.email
    assert response_data['data'][0]['display_name'] == test_user_data.display_name
    assert response_data['data'][0]['id'] == user_id
    assert response_data['data'][0]['created_at'] is not None
    assert response_data['data'][0]['updated_at'] is not None
