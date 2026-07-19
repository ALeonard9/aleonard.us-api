# pylint: disable=missing-module-docstring, missing-function-docstring
from fastapi.testclient import TestClient


def _auth(test_client: TestClient) -> dict:
    return {'Authorization': f'Bearer {test_client.first_user.token}'}


def _show_with_episode(test_client: TestClient):
    admin = {'Authorization': f'Bearer {test_client.admin_user.token}'}
    show_id = test_client.post(
        '/v1/tv-shows', headers=admin, json={'title': 'Severance', 'imdb': 'tt11280740'}
    ).json()['id']
    episode_id = test_client.post(
        f'/v1/tv-shows/{show_id}/episodes',
        headers=admin,
        json={'title': 'Good News About Hell', 'season': 1, 'season_number': 1},
    ).json()['id']
    return show_id, episode_id


def test_marking_watched_stamps_watched_at(test_client: TestClient):
    _, episode_id = _show_with_episode(test_client)
    body = test_client.post(
        f'/v1/users/me/episodes/{episode_id}', headers=_auth(test_client)
    ).json()
    assert body['watched'] == 1
    assert body['watched_at'] is not None


def test_remarking_preserves_original_watched_at(test_client: TestClient):
    _, episode_id = _show_with_episode(test_client)
    first = test_client.post(
        f'/v1/users/me/episodes/{episode_id}', headers=_auth(test_client)
    ).json()['watched_at']
    second = test_client.post(
        f'/v1/users/me/episodes/{episode_id}', headers=_auth(test_client)
    ).json()['watched_at']
    assert second == first


def test_watch_all_stamps_watched_at(test_client: TestClient):
    show_id, _ = _show_with_episode(test_client)
    marks = test_client.post(
        f'/v1/users/me/tv-shows/{show_id}/episodes/watch-all',
        headers=_auth(test_client),
    ).json()
    assert marks and all(m['watched_at'] is not None for m in marks)
