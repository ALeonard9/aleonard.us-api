"""
Tests the user API calls
"""

from typing import Callable

from fastapi.testclient import TestClient


def test_api_create_user(
    test_client: TestClient, test_user_data_generator: Callable[..., list]
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
    response = test_client.post('/v1/users/', json=user_data)

    print(response.json())
    assert response.status_code == 201
    response_data = response.json()
    assert response_data['success'] is True
    assert response_data['message'] == 'User created'
    assert response_data['data'][0]['email'] == test_user_data.email
    assert response_data['data'][0]['display_name'] == test_user_data.display_name


def test_api_get_user(
    test_client: TestClient,
    test_create_user: Callable[..., list],
    test_authenticate_user: Callable[..., str],
):
    """
    Test getting a user.
    """

    users = test_create_user(test_client, user_count=1)
    user_id = users[0].id
    token = test_authenticate_user(test_client, users[0].email, users[0].plain_password)
    assert token is not None

    headers = {'Authorization': f"Bearer {token}"}
    get_response = test_client.get(f"/v1/users/{user_id}", headers=headers)

    assert get_response.status_code == 200
    response_data = get_response.json()
    assert response_data['success'] is True
    assert response_data['message'] == 'User found'
    assert response_data['data'][0]['email'] == users[0].email
    assert response_data['data'][0]['display_name'] == users[0].display_name
    assert response_data['data'][0]['id'] == user_id
    assert response_data['data'][0]['created_at'] is not None
    assert response_data['data'][0]['updated_at'] is not None


def test_api_get_all_users(
    test_client: TestClient,
    test_create_user: Callable[..., list],
):
    """
    Test listing all users.
    """
    _test_users = test_create_user(test_client, user_count=3)
    token = test_client.admin_token

    # List users
    headers = {'Authorization': f"Bearer {token}"}
    list_response = test_client.get('/v1/users/', headers=headers)
    assert list_response.status_code == 200
    response_data = list_response.json()
    assert response_data['success'] is True
    assert response_data['message'] == 'Users found'
    # Verify we have at least three users in the response
    assert len(response_data['data']) >= 3


def test_api_update_user(
    test_client: TestClient,
    test_create_user: Callable[..., list],
    test_authenticate_user: Callable[..., str],
    test_user_data_generator: Callable[..., list],
):
    """
    Test updating a user.
    """
    # Create original user
    users = test_create_user(test_client, user_count=1)
    user_data_list = test_user_data_generator(num_users=1)
    update_user_data = user_data_list[0]
    user_id = users[0].id

    # Authenticate original user
    token = test_authenticate_user(test_client, users[0].email, users[0].plain_password)
    assert token is not None

    # Update user
    updated_payload = {
        'display_name': update_user_data.display_name,
        'email': update_user_data.email,
        'password': update_user_data.password,
    }
    headers = {'Authorization': f"Bearer {token}"}
    put_response = test_client.put(
        f"/v1/users/{user_id}", json=updated_payload, headers=headers
    )
    assert put_response.status_code == 200
    put_data = put_response.json()
    assert put_data['data'][0]['email'] == update_user_data.email
    assert put_data['data'][0]['display_name'] == update_user_data.display_name


def test_api_delete_user(
    test_client: TestClient,
    test_create_user: Callable[..., list],
    test_authenticate_user: Callable[..., str],
):
    """
    Test deleting a user.
    """
    # Create user
    users = test_create_user(test_client, user_count=1)
    user_id = users[0].id

    # Authenticate user
    token = test_authenticate_user(test_client, users[0].email, users[0].plain_password)
    assert token is not None

    # Delete user
    headers = {'Authorization': f"Bearer {token}"}
    del_response = test_client.delete(f"/v1/users/{user_id}", headers=headers)
    assert del_response.status_code == 200
    del_data = del_response.json()
    assert del_data['success'] is True
    assert del_data['message'] == 'User deleted'
