# pylint: disable=missing-module-docstring, missing-function-docstring
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient


def _iso(delta_days: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=delta_days)).isoformat()


def _make_movie(
    test_client: TestClient, imdb='tt1375666', title='Inception', **extra
) -> str:
    headers = {'Authorization': f"Bearer {test_client.admin_user.token}"}
    resp = test_client.post(
        '/v1/movies', headers=headers, json={'title': title, 'imdb': imdb, **extra}
    )
    assert resp.status_code == 201
    return resp.json()['id']


def _watchlist(test_client: TestClient, movie_id: str) -> None:
    headers = {'Authorization': f"Bearer {test_client.first_user.token}"}
    resp = test_client.post(
        f"/v1/users/me/movies/{movie_id}", headers=headers, json={'on_watchlist': True}
    )
    assert resp.status_code == 201


def test_release_within_week_creates_notification(test_client: TestClient):
    movie_id = _make_movie(test_client, release_date=_iso(3))
    _watchlist(test_client, movie_id)
    headers = {'Authorization': f"Bearer {test_client.first_user.token}"}

    resp = test_client.get('/v1/users/me/notifications', headers=headers)
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 1
    assert items[0]['type'] == 'movie_release'
    assert items[0]['category'] == 'movie'
    assert items[0]['entity_id'] == movie_id
    assert items[0]['read'] is False
    assert 'Inception' in items[0]['title']


def test_release_sweep_is_idempotent(test_client: TestClient):
    movie_id = _make_movie(test_client, release_date=_iso(3))
    _watchlist(test_client, movie_id)
    headers = {'Authorization': f"Bearer {test_client.first_user.token}"}

    test_client.get('/v1/users/me/notifications', headers=headers)
    resp = test_client.get('/v1/users/me/notifications', headers=headers)
    assert len(resp.json()) == 1


def test_release_outside_week_ignored(test_client: TestClient):
    far = _make_movie(test_client, imdb='tt1', title='Far Out', release_date=_iso(30))
    past = _make_movie(test_client, imdb='tt2', title='Old One', release_date=_iso(-30))
    _watchlist(test_client, far)
    _watchlist(test_client, past)
    headers = {'Authorization': f"Bearer {test_client.first_user.token}"}

    resp = test_client.get('/v1/users/me/notifications', headers=headers)
    assert resp.json() == []


def test_release_not_on_watchlist_ignored(test_client: TestClient):
    movie_id = _make_movie(test_client, release_date=_iso(3))
    headers = {'Authorization': f"Bearer {test_client.first_user.token}"}
    # Ranked (already seen) rather than on the to-see list.
    test_client.post(
        f"/v1/users/me/movies/{movie_id}", headers=headers, json={'on_rankings': True}
    )

    resp = test_client.get('/v1/users/me/notifications', headers=headers)
    assert resp.json() == []


def test_unread_count_and_mark_read(test_client: TestClient):
    movie_id = _make_movie(test_client, release_date=_iso(3))
    _watchlist(test_client, movie_id)
    headers = {'Authorization': f"Bearer {test_client.first_user.token}"}

    count = test_client.get('/v1/users/me/notifications/unread-count', headers=headers)
    assert count.json() == {'unread': 1}

    items = test_client.get('/v1/users/me/notifications', headers=headers).json()
    marked = test_client.put(
        f"/v1/users/me/notifications/{items[0]['id']}/read", headers=headers
    )
    assert marked.status_code == 200
    assert marked.json()['read'] is True

    count = test_client.get('/v1/users/me/notifications/unread-count', headers=headers)
    assert count.json() == {'unread': 0}


def test_mark_all_read(test_client: TestClient):
    first = _make_movie(test_client, imdb='tt1', title='One', release_date=_iso(2))
    second = _make_movie(test_client, imdb='tt2', title='Two', release_date=_iso(5))
    _watchlist(test_client, first)
    _watchlist(test_client, second)
    headers = {'Authorization': f"Bearer {test_client.first_user.token}"}

    count = test_client.get('/v1/users/me/notifications/unread-count', headers=headers)
    assert count.json() == {'unread': 2}

    resp = test_client.put('/v1/users/me/notifications/read-all', headers=headers)
    assert resp.json() == {'unread': 0}

    items = test_client.get(
        '/v1/users/me/notifications', headers=headers, params={'unread_only': True}
    )
    assert items.json() == []


def test_mark_read_other_users_notification_404s(test_client: TestClient):
    movie_id = _make_movie(test_client, release_date=_iso(3))
    _watchlist(test_client, movie_id)
    user_headers = {'Authorization': f"Bearer {test_client.first_user.token}"}
    admin_headers = {'Authorization': f"Bearer {test_client.admin_user.token}"}

    items = test_client.get('/v1/users/me/notifications', headers=user_headers).json()
    resp = test_client.put(
        f"/v1/users/me/notifications/{items[0]['id']}/read", headers=admin_headers
    )
    assert resp.status_code == 404


def test_notifications_require_auth(test_client: TestClient):
    assert test_client.get('/v1/users/me/notifications').status_code == 401
    assert test_client.get('/v1/users/me/notifications/unread-count').status_code == 401
