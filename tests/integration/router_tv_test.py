# pylint: disable=missing-module-docstring, missing-function-docstring
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient


def _make_show(test_client: TestClient, title='Breaking Bad', **extra) -> str:
    headers = {'Authorization': f"Bearer {test_client.admin_user.token}"}
    resp = test_client.post(
        '/v1/tv-shows', headers=headers, json={'title': title, **extra}
    )
    assert resp.status_code == 201
    return resp.json()['id']


def _make_episode(
    test_client: TestClient, show_id: str, title='Pilot', season=1, number=1
) -> str:
    headers = {'Authorization': f"Bearer {test_client.admin_user.token}"}
    resp = test_client.post(
        f"/v1/tv-shows/{show_id}/episodes",
        headers=headers,
        json={'title': title, 'season': season, 'season_number': number},
    )
    assert resp.status_code == 201
    return resp.json()['id']


# --- Global catalog ---
def test_create_tv_show(test_client: TestClient):
    admin_headers = {'Authorization': f"Bearer {test_client.admin_user.token}"}
    response = test_client.post(
        '/v1/tv-shows',
        headers=admin_headers,
        json={'title': 'Breaking Bad', 'imdb': 'tt0903747'},
    )
    assert response.status_code == 201
    data = response.json()
    assert data['title'] == 'Breaking Bad'
    assert data['imdb'] == 'tt0903747'


def test_get_tv_shows(test_client: TestClient):
    _make_show(test_client)
    response = test_client.get('/v1/tv-shows')
    assert response.status_code == 200
    assert len(response.json()) > 0


def test_create_tv_show_unauthenticated(test_client: TestClient):
    response = test_client.post('/v1/tv-shows', json={'title': 'Breaking Bad'})
    assert response.status_code == 401


def test_create_tv_show_requires_admin(test_client: TestClient):
    headers = {'Authorization': f"Bearer {test_client.first_user.token}"}
    response = test_client.post(
        '/v1/tv-shows', headers=headers, json={'title': 'Breaking Bad'}
    )
    assert response.status_code == 403


def test_create_duplicate_tvmaze_rejected(test_client: TestClient):
    admin_headers = {'Authorization': f"Bearer {test_client.admin_user.token}"}
    with patch('app.router.v1.router_tv.get_tv_show_detail', return_value=None):
        first = test_client.post(
            '/v1/tv-shows',
            headers=admin_headers,
            json={'title': 'Severance', 'tvmaze': 44932},
        )
        assert first.status_code == 201
        dup = test_client.post(
            '/v1/tv-shows',
            headers=admin_headers,
            json={'title': 'Severance again', 'tvmaze': 44932},
        )
    assert dup.status_code == 400


def test_update_tv_show_requires_admin(test_client: TestClient):
    show_id = _make_show(test_client)
    headers = {'Authorization': f"Bearer {test_client.first_user.token}"}
    response = test_client.put(
        f"/v1/tv-shows/{show_id}", headers=headers, json={'title': 'Hacked'}
    )
    assert response.status_code == 403


@patch('app.router.v1.router_tv.get_tv_show_detail')
def test_get_tv_show_enriches_on_view(mock_detail, test_client: TestClient):
    show_id = _make_show(test_client)
    mock_detail.return_value = {
        'status': 'Ended',
        'genre': 'Crime, Drama, Thriller',
        'network': 'AMC',
        'year': 2008,
        'rating': 9.2,
        'summary': 'A chemistry teacher breaks bad.',
    }
    headers = {'Authorization': f"Bearer {test_client.first_user.token}"}
    resp = test_client.get(f"/v1/tv-shows/{show_id}", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data['genre'] == 'Crime, Drama, Thriller'
    assert data['network'] == 'AMC'
    assert data['year'] == 2008
    assert data['summary'] == 'A chemistry teacher breaks bad.'


# --- Search proxy ---
def test_search_tv_shows_requires_auth(test_client: TestClient):
    response = test_client.get('/v1/tv-shows/search?q=severance')
    assert response.status_code == 401


@patch('app.services.tv_search.requests.get')
def test_search_tv_shows_returns_results(mock_get, test_client: TestClient):
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = [
        {
            'score': 0.9,
            'show': {
                'id': 44932,
                'name': 'Severance',
                'premiered': '2022-02-18',
                'status': 'Running',
                'externals': {'imdb': 'tt11280740'},
                'network': None,
                'webChannel': {'name': 'Apple TV+'},
                'image': {'medium': 'https://x/m.jpg', 'original': 'https://x/o.jpg'},
            },
        }
    ]
    mock_get.return_value = mock_response

    headers = {'Authorization': f"Bearer {test_client.first_user.token}"}
    response = test_client.get('/v1/tv-shows/search?q=severance', headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]['tvmaze'] == 44932
    assert data[0]['imdb'] == 'tt11280740'
    assert data[0]['title'] == 'Severance'
    assert data[0]['year'] == '2022'
    assert data[0]['network'] == 'Apple TV+'
    assert data[0]['poster_url'] == 'https://x/o.jpg'


# --- Show trackers (Movies-parity lists) ---
def test_mark_show_to_rankings_is_unplaced(test_client: TestClient):
    show_id = _make_show(test_client)
    headers = {'Authorization': f"Bearer {test_client.first_user.token}"}
    response = test_client.post(
        f"/v1/users/me/tv-shows/{show_id}",
        headers=headers,
        json={'on_rankings': True, 'notes': 'Peak TV'},
    )
    assert response.status_code == 201
    data = response.json()
    assert data['on_rankings'] is True
    assert data['on_watchlist'] is False
    assert data['rank'] is None
    assert data['notes'] == 'Peak TV'


def test_lists_are_independent(test_client: TestClient):
    show_id = _make_show(test_client)
    headers = {'Authorization': f"Bearer {test_client.first_user.token}"}

    r = test_client.post(
        f"/v1/users/me/tv-shows/{show_id}",
        headers=headers,
        json={'on_watchlist': True},
    )
    assert r.json()['on_watchlist'] is True
    assert r.json()['on_rankings'] is False

    r = test_client.post(
        f"/v1/users/me/tv-shows/{show_id}",
        headers=headers,
        json={'on_rankings': True},
    )
    assert r.json()['on_watchlist'] is True
    assert r.json()['on_rankings'] is True
    assert r.json()['rank'] is None

    r = test_client.put(
        f"/v1/users/me/tv-shows/{show_id}",
        headers=headers,
        json={'on_rankings': False},
    )
    assert r.json()['on_watchlist'] is True
    assert r.json()['on_rankings'] is False

    # Off both lists -> tracker dropped.
    test_client.put(
        f"/v1/users/me/tv-shows/{show_id}",
        headers=headers,
        json={'on_watchlist': False},
    )
    listing = test_client.get('/v1/users/me/tv-shows', headers=headers).json()
    assert all(t['tv_show']['id'] != show_id for t in listing)


def test_set_show_rank_inserts_and_shifts(test_client: TestClient):
    headers = {'Authorization': f"Bearer {test_client.first_user.token}"}
    ids = []
    for i in range(3):
        sid = _make_show(test_client, title=f"Ranked {i}")
        test_client.post(
            f"/v1/users/me/tv-shows/{sid}",
            headers=headers,
            json={'on_rankings': True},
        )
        ids.append(sid)
    test_client.put(
        '/v1/users/me/tv-shows/rankings/order',
        headers=headers,
        json={'show_ids': ids},
    )

    new_id = _make_show(test_client, title='Inserted')
    test_client.post(
        f"/v1/users/me/tv-shows/{new_id}",
        headers=headers,
        json={'on_rankings': True},
    )
    resp = test_client.put(
        f"/v1/users/me/tv-shows/{new_id}/rank",
        headers=headers,
        json={'position': 2},
    )
    assert resp.status_code == 200
    assert resp.json()['rank'] == 2

    listing = test_client.get('/v1/users/me/tv-shows', headers=headers).json()
    ranked = sorted(
        [t for t in listing if t['rank'] is not None], key=lambda t: t['rank']
    )
    order = [(t['rank'], t['tv_show']['id']) for t in ranked]
    assert order == [(1, ids[0]), (2, new_id), (3, ids[1]), (4, ids[2])]


def test_reorder_rankings(test_client: TestClient):
    headers = {'Authorization': f"Bearer {test_client.first_user.token}"}
    ids = []
    for i in range(3):
        sid = _make_show(test_client, title=f"Show {i}")
        test_client.post(
            f"/v1/users/me/tv-shows/{sid}",
            headers=headers,
            json={'on_rankings': True},
        )
        ids.append(sid)

    reordered = list(reversed(ids))
    resp = test_client.put(
        '/v1/users/me/tv-shows/rankings/order',
        headers=headers,
        json={'show_ids': reordered},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert [t['tv_show']['id'] for t in data] == reordered
    assert [t['rank'] for t in data] == [1, 2, 3]


def test_reentering_rankings_starts_unplaced(test_client: TestClient):
    show_id = _make_show(test_client)
    headers = {'Authorization': f"Bearer {test_client.first_user.token}"}
    test_client.post(
        f"/v1/users/me/tv-shows/{show_id}", headers=headers, json={'on_rankings': True}
    )
    test_client.put(
        f"/v1/users/me/tv-shows/{show_id}/rank", headers=headers, json={'position': 1}
    )
    test_client.put(
        f"/v1/users/me/tv-shows/{show_id}",
        headers=headers,
        json={'on_watchlist': True, 'on_rankings': False},
    )
    r = test_client.post(
        f"/v1/users/me/tv-shows/{show_id}", headers=headers, json={'on_rankings': True}
    )
    assert r.json()['on_rankings'] is True
    assert r.json()['rank'] is None


# --- Episodes ---
def test_create_episode(test_client: TestClient):
    show_id = _make_show(test_client)
    episode_id = _make_episode(test_client, show_id)
    assert episode_id

    listing = test_client.get(f"/v1/tv-shows/{show_id}/episodes")
    assert listing.status_code == 200
    data = listing.json()
    assert len(data) == 1
    assert data[0]['title'] == 'Pilot'
    assert data[0]['season'] == 1


@patch('app.services.tv_search.get_show_episodes')
def test_sync_episodes_upserts(mock_episodes, test_client: TestClient):
    admin_headers = {'Authorization': f"Bearer {test_client.admin_user.token}"}
    with patch('app.router.v1.router_tv.get_tv_show_detail', return_value=None):
        show_id = _make_show(test_client, title='Severance', tvmaze=44932)
    mock_episodes.return_value = [
        {
            'tvmaze': 2128885,
            'title': 'Good News About Hell',
            'season': 1,
            'season_number': 1,
            'airdate': None,
        },
        {
            'tvmaze': 2128886,
            'title': 'Half Loop',
            'season': 1,
            'season_number': 2,
            'airdate': None,
        },
    ]
    resp = test_client.post(
        f"/v1/tv-shows/{show_id}/episodes/sync", headers=admin_headers
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 2

    # Re-sync is idempotent (upsert, not duplicate).
    resp = test_client.post(
        f"/v1/tv-shows/{show_id}/episodes/sync", headers=admin_headers
    )
    assert len(resp.json()) == 2


def test_mark_and_unmark_episode_watched(test_client: TestClient):
    show_id = _make_show(test_client)
    episode_id = _make_episode(test_client, show_id)
    headers = {'Authorization': f"Bearer {test_client.first_user.token}"}

    resp = test_client.post(f"/v1/users/me/episodes/{episode_id}", headers=headers)
    assert resp.status_code == 201
    assert resp.json()['watched'] == 1

    # Idempotent re-mark.
    resp = test_client.post(f"/v1/users/me/episodes/{episode_id}", headers=headers)
    assert resp.status_code == 201
    assert resp.json()['watched'] == 1

    listing = test_client.get(
        f"/v1/users/me/tv-shows/{show_id}/episodes", headers=headers
    )
    assert listing.status_code == 200
    assert len(listing.json()) == 1

    resp = test_client.delete(f"/v1/users/me/episodes/{episode_id}", headers=headers)
    assert resp.status_code == 204

    resp = test_client.delete(f"/v1/users/me/episodes/{episode_id}", headers=headers)
    assert resp.status_code == 404


def test_user_episode_marks_are_per_user(test_client: TestClient):
    show_id = _make_show(test_client)
    episode_id = _make_episode(test_client, show_id)
    first = {'Authorization': f"Bearer {test_client.first_user.token}"}
    second = {'Authorization': f"Bearer {test_client.second_user.token}"}

    test_client.post(f"/v1/users/me/episodes/{episode_id}", headers=first)
    listing = test_client.get(
        f"/v1/users/me/tv-shows/{show_id}/episodes", headers=second
    )
    assert listing.json() == []
