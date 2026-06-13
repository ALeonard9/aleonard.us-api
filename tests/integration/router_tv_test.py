# pylint: disable=missing-module-docstring, missing-function-docstring
from fastapi.testclient import TestClient


def test_create_tv_show(test_client: TestClient):
    admin_token = test_client.admin_user.token
    headers = {'Authorization': f"Bearer {admin_token}"}
    response = test_client.post(
        '/v1/tv-shows',
        headers=headers,
        json={'title': 'Breaking Bad', 'imdb': 'tt0903747'},
    )
    assert response.status_code == 201
    data = response.json()
    assert data['title'] == 'Breaking Bad'


def test_create_episode(test_client: TestClient):
    admin_token = test_client.admin_user.token
    headers = {'Authorization': f"Bearer {admin_token}"}

    # Create Show
    response = test_client.post(
        '/v1/tv-shows',
        headers=headers,
        json={'title': 'Breaking Bad', 'imdb': 'tt0903747'},
    )
    show_id = response.json()['id']

    # Create Episode
    response = test_client.post(
        f"/v1/tv-shows/{show_id}/episodes",
        headers=headers,
        json={'title': 'Pilot', 'season': 1, 'season_number': 1},
    )
    assert response.status_code == 201
    data = response.json()
    assert data['title'] == 'Pilot'
    assert data['season'] == 1


def test_mark_tv_show_and_episode(test_client: TestClient):
    admin_token = test_client.admin_user.token
    headers = {'Authorization': f"Bearer {admin_token}"}

    # Create Show
    response = test_client.post(
        '/v1/tv-shows',
        headers=headers,
        json={'title': 'Breaking Bad', 'imdb': 'tt0903747'},
    )
    show_id = response.json()['id']

    # Create Episode
    response = test_client.post(
        f"/v1/tv-shows/{show_id}/episodes",
        headers=headers,
        json={'title': 'Pilot', 'season': 1, 'season_number': 1},
    )
    episode_id = response.json()['id']

    user_token = test_client.first_user.token
    user_headers = {'Authorization': f"Bearer {user_token}"}

    # Mark Show
    response = test_client.post(
        f"/v1/users/me/tv-shows/{show_id}", headers=user_headers, json={'rank': 1}
    )
    assert response.status_code == 201

    # Mark Episode
    response = test_client.post(
        f"/v1/users/me/episodes/{episode_id}", headers=user_headers, json={'watched': 1}
    )
    assert response.status_code == 201
    assert response.json()['watched'] == 1
