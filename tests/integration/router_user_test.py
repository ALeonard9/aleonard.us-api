"""
Tests the user API calls
"""

from typing import Callable

from faker import Faker
from fastapi.testclient import TestClient

fake = Faker()


def test_api_create_user(
    test_client: TestClient,
    test_user_data_generator: Callable[..., list],
    test_assert_timestamps: Callable[..., None],
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
    assert response_data['data'][0]['user_group'] == 'user'
    test_assert_timestamps(response_data['data'][0])


def test_api_user_get_user(
    test_client: TestClient,
    test_assert_timestamps: Callable[..., None],
):
    """
    Test user getting a themself.
    """
    user_id = test_client.first_user.id
    token = test_client.first_user.token

    headers = {'Authorization': f"Bearer {token}"}
    response = test_client.get(f"/v1/users/{user_id}", headers=headers)

    assert response.status_code == 200
    response_data = response.json()
    assert response_data['success'] is True
    assert response_data['message'] == 'User found'
    assert response_data['data'][0]['id'] == test_client.first_user.id
    assert response_data['data'][0]['email'] == test_client.first_user.email
    assert (
        response_data['data'][0]['display_name'] == test_client.first_user.display_name
    )
    assert response_data['data'][0]['user_group'] == 'user'
    test_assert_timestamps(response_data['data'][0])


def test_api_admin_get_user(
    test_client: TestClient,
    test_assert_timestamps: Callable[..., None],
):
    """
    Test admin getting a user.
    """
    user_id = test_client.first_user.id
    token = test_client.admin_user.token

    headers = {'Authorization': f"Bearer {token}"}
    response = test_client.get(f"/v1/users/{user_id}", headers=headers)

    assert response.status_code == 200
    response_data = response.json()
    assert response_data['success'] is True
    assert response_data['message'] == 'User found'
    assert response_data['data'][0]['id'] == test_client.first_user.id
    assert response_data['data'][0]['email'] == test_client.first_user.email
    assert (
        response_data['data'][0]['display_name'] == test_client.first_user.display_name
    )
    assert response_data['data'][0]['user_group'] == 'user'
    test_assert_timestamps(response_data['data'][0])


def test_api_admin_cant_get_unknown_user(
    test_client: TestClient,
):
    """
    Test admin unable to get an unknown user.
    """
    user_id = fake.uuid4()
    token = test_client.admin_user.token

    headers = {'Authorization': f"Bearer {token}"}
    response = test_client.get(f"/v1/users/{user_id}", headers=headers)

    assert response.status_code == 404
    response_data = response.json()
    assert response_data['success'] is False
    assert response_data['message'] == f'User with id {user_id} not found'
    assert response_data['data'] == []


def test_api_user_cant_get_other_user(
    test_client: TestClient,
):
    """
    Test user unable to get other a user.
    """
    user_id = test_client.first_user.id
    token = test_client.second_user.token

    headers = {'Authorization': f"Bearer {token}"}
    response = test_client.get(f"/v1/users/{user_id}", headers=headers)

    assert response.status_code == 403
    response_data = response.json()
    assert response_data['success'] is False
    assert response_data['message'] == 'User can only view their own account.'
    assert response_data['data'] == []


def test_api_admin_get_all_users(
    test_client: TestClient,
):
    """
    Test admin can listing all users.
    """
    token = test_client.admin_user.token
    headers = {'Authorization': f"Bearer {token}"}
    list_response = test_client.get('/v1/users/', headers=headers)
    assert list_response.status_code == 200
    response_data = list_response.json()
    assert response_data['success'] is True
    assert response_data['message'] == 'Users found'
    # Verify we have at least three users in the response.
    # Pre-loaded users are admin, user1, and user2
    assert len(response_data['data']) >= 3


def test_api_user_cant_get_all_users(
    test_client: TestClient,
    # test_create_user: Callable[..., list],
):
    """
    Test user unable to list all users.
    """
    token = test_client.first_user.token
    headers = {'Authorization': f"Bearer {token}"}
    list_response = test_client.get('/v1/users/', headers=headers)
    assert list_response.status_code == 403
    response_data = list_response.json()
    assert response_data['success'] is False
    assert (
        response_data['message'] == 'User does not have permission to view all users.'
    )


def test_api_admin_update_user(
    test_client: TestClient,
    test_user_data_generator: Callable[..., list],
    test_assert_timestamps: Callable[..., None],
):
    """
    Test admin updating a user.
    """

    update_user_data = test_user_data_generator(num_users=1)[0]

    user_id = test_client.first_user.id
    token = test_client.admin_user.token

    # Update user
    updated_payload = {
        'display_name': update_user_data.display_name,
        'email': update_user_data.email,
        'password': update_user_data.password,
    }
    headers = {'Authorization': f"Bearer {token}"}
    response = test_client.put(
        f"/v1/users/{user_id}", json=updated_payload, headers=headers
    )
    assert response.status_code == 200
    response_data = response.json()
    assert response_data['success'] is True
    assert response_data['message'] == 'User updated'
    assert response_data['data'][0]['id'] == test_client.first_user.id
    assert response_data['data'][0]['email'] == update_user_data.email
    assert response_data['data'][0]['display_name'] == update_user_data.display_name
    assert response_data['data'][0]['user_group'] == 'user'
    test_assert_timestamps(response_data['data'][0])


def test_api_user_update_self(
    test_client: TestClient,
    test_user_data_generator: Callable[..., list],
    test_assert_timestamps: Callable[..., None],
):
    """
    Test updating a user.
    """

    update_user_data = test_user_data_generator(num_users=1)[0]

    user_id = test_client.first_user.id
    token = test_client.first_user.token

    # Update user
    updated_payload = {
        'display_name': update_user_data.display_name,
        'email': update_user_data.email,
        'password': update_user_data.password,
    }
    headers = {'Authorization': f"Bearer {token}"}
    response = test_client.put(
        f"/v1/users/{user_id}", json=updated_payload, headers=headers
    )
    assert response.status_code == 200
    response_data = response.json()
    assert response_data['success'] is True
    assert response_data['message'] == 'User updated'
    assert response_data['data'][0]['id'] == test_client.first_user.id
    assert response_data['data'][0]['email'] == update_user_data.email
    assert response_data['data'][0]['display_name'] == update_user_data.display_name
    assert response_data['data'][0]['user_group'] == 'user'
    test_assert_timestamps(response_data['data'][0])


def test_api_user_cant_update_other(
    test_client: TestClient,
    test_user_data_generator: Callable[..., list],
):
    """
    Test user unable to update other user.
    """

    update_user_data = test_user_data_generator(num_users=1)[0]

    user_id = test_client.first_user.id
    token = test_client.second_user.token

    # Update user
    updated_payload = {
        'display_name': update_user_data.display_name,
        'email': update_user_data.email,
        'password': update_user_data.password,
    }
    headers = {'Authorization': f"Bearer {token}"}
    response = test_client.put(
        f"/v1/users/{user_id}", json=updated_payload, headers=headers
    )
    assert response.status_code == 403
    response_data = response.json()
    assert response_data['success'] is False
    assert response_data['message'] == 'User can only update their own account.'
    assert response_data['data'] == []


def test_api_user_cant_update_unknown_other(
    test_client: TestClient,
    test_user_data_generator: Callable[..., list],
):
    """
    Test admin unable to update unknown user.
    """

    update_user_data = test_user_data_generator(num_users=1)[0]

    user_id = fake.uuid4()
    token = test_client.admin_user.token

    # Update user
    updated_payload = {
        'display_name': update_user_data.display_name,
        'email': update_user_data.email,
        'password': update_user_data.password,
    }
    headers = {'Authorization': f"Bearer {token}"}
    response = test_client.put(
        f"/v1/users/{user_id}", json=updated_payload, headers=headers
    )
    assert response.status_code == 404
    response_data = response.json()
    assert response_data['success'] is False
    assert response_data['message'] == f'User with id {user_id} not found'
    assert response_data['data'] == []


def test_api_admin_delete_user(
    test_client: TestClient,
    test_assert_timestamps: Callable[..., None],
):
    """
    Test admin deleting a user.
    """
    user_id = test_client.first_user.id
    token = test_client.admin_user.token
    # Delete user
    headers = {'Authorization': f"Bearer {token}"}
    response = test_client.delete(f"/v1/users/{user_id}", headers=headers)
    assert response.status_code == 200
    response_data = response.json()
    assert response_data['success'] is True
    assert response_data['message'] == 'User deleted'
    assert response_data['data'][0]['id'] == test_client.first_user.id
    assert response_data['data'][0]['email'] == test_client.first_user.email
    assert (
        response_data['data'][0]['display_name'] == test_client.first_user.display_name
    )
    assert response_data['data'][0]['user_group'] == 'user'
    test_assert_timestamps(response_data['data'][0])


def test_api_user_delete_self(
    test_client: TestClient,
    test_assert_timestamps: Callable[..., None],
):
    """
    Test deleting a user.
    """
    user_id = test_client.first_user.id
    token = test_client.first_user.token
    # Delete user
    headers = {'Authorization': f"Bearer {token}"}
    response = test_client.delete(f"/v1/users/{user_id}", headers=headers)
    assert response.status_code == 200
    response_data = response.json()
    assert response_data['success'] is True
    assert response_data['message'] == 'User deleted'
    assert response_data['data'][0]['id'] == test_client.first_user.id
    assert response_data['data'][0]['email'] == test_client.first_user.email
    assert (
        response_data['data'][0]['display_name'] == test_client.first_user.display_name
    )
    assert response_data['data'][0]['user_group'] == 'user'
    test_assert_timestamps(response_data['data'][0])


def test_api_user_cant_delete_other(
    test_client: TestClient,
):
    """
    Test user unable to delete other user.
    """
    user_id = test_client.first_user.id
    token = test_client.second_user.token
    headers = {'Authorization': f"Bearer {token}"}
    response = test_client.delete(f"/v1/users/{user_id}", headers=headers)
    assert response.status_code == 403
    response_data = response.json()
    assert response_data['success'] is False
    assert response_data['message'] == 'User can only delete their own account.'
    assert response_data['data'] == []


def test_api_admin_cant_delete_unknown_other(
    test_client: TestClient,
):
    """
    Test admin unable to delete unknown user.
    """
    user_id = fake.uuid4()
    token = test_client.admin_user.token
    headers = {'Authorization': f"Bearer {token}"}
    response = test_client.delete(f"/v1/users/{user_id}", headers=headers)
    assert response.status_code == 404
    response_data = response.json()
    assert response_data['success'] is False
    assert response_data['message'] == f'User with id {user_id} not found'
    assert response_data['data'] == []
