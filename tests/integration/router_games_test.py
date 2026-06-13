import pytest
from fastapi.testclient import TestClient


def test_create_game(test_client: TestClient):
    admin_token = test_client.admin_user.token
    headers = {'Authorization': f"Bearer {admin_token}"}
    response = test_client.post(
        '/v1/games',
        headers=headers,
        json={'title': 'Zelda: Breath of the Wild', 'igdb': 1111},
    )
    assert response.status_code == 201
    data = response.json()
    assert data['title'] == 'Zelda: Breath of the Wild'
    assert data['igdb'] == 1111


def test_mark_game(test_client: TestClient):
    admin_token = test_client.admin_user.token
    headers = {'Authorization': f"Bearer {admin_token}"}

    response = test_client.post(
        '/v1/games', headers=headers, json={'title': 'Zelda', 'igdb': 1111}
    )
    game_id = response.json()['id']

    user_token = test_client.first_user.token
    user_headers = {'Authorization': f"Bearer {user_token}"}

    response = test_client.post(
        f"/v1/users/me/games/{game_id}",
        headers=user_headers,
        json={'rank': 1, 'is_100_percent': True},
    )
    assert response.status_code == 201
    data = response.json()
    assert data['rank'] == 1
    assert data['is_100_percent'] is True
