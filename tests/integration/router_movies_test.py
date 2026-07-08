# pylint: disable=missing-module-docstring, missing-function-docstring
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.config import Settings


def test_create_movie(test_client: TestClient):
    admin_token = test_client.admin_user.token
    headers = {'Authorization': f"Bearer {admin_token}"}
    response = test_client.post(
        '/v1/movies', headers=headers, json={'title': 'Inception', 'imdb': 'tt1375666'}
    )
    assert response.status_code == 201
    data = response.json()
    assert data['title'] == 'Inception'
    assert data['imdb'] == 'tt1375666'


def test_get_movies(test_client: TestClient):
    admin_token = test_client.admin_user.token
    headers = {'Authorization': f"Bearer {admin_token}"}
    test_client.post(
        '/v1/movies', headers=headers, json={'title': 'Inception', 'imdb': 'tt1375666'}
    )

    response = test_client.get('/v1/movies')
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0


def _make_movie(test_client: TestClient, imdb='tt1375666', title='Inception') -> str:
    headers = {'Authorization': f"Bearer {test_client.admin_user.token}"}
    resp = test_client.post(
        '/v1/movies', headers=headers, json={'title': title, 'imdb': imdb}
    )
    return resp.json()['id']


def test_mark_movie_to_rankings_is_unplaced(test_client: TestClient):
    """Adding to Rankings leaves the movie unplaced (rank None) until positioned."""
    movie_id = _make_movie(test_client)
    user_headers = {'Authorization': f"Bearer {test_client.first_user.token}"}

    response = test_client.post(
        f"/v1/users/me/movies/{movie_id}",
        headers=user_headers,
        json={'on_rankings': True, 'notes': 'Mind-bending!'},
    )
    assert response.status_code == 201
    data = response.json()
    assert data['on_rankings'] is True
    assert data['on_watchlist'] is False
    assert data['rank'] is None
    assert data['notes'] == 'Mind-bending!'


def test_set_movie_rank_inserts_and_shifts(test_client: TestClient):
    """Placing a movie at position N shifts existing movies at/after N down."""
    user_headers = {'Authorization': f"Bearer {test_client.first_user.token}"}
    ids = []
    for i in range(3):
        mid = _make_movie(test_client, imdb=f"tt700{i}", title=f"Ranked {i}")
        test_client.post(
            f"/v1/users/me/movies/{mid}",
            headers=user_headers,
            json={'on_rankings': True},
        )
        ids.append(mid)
    # Establish an initial 1..3 order.
    test_client.put(
        '/v1/users/me/movies/rankings/order',
        headers=user_headers,
        json={'movie_ids': ids},
    )

    # A fresh movie, added to rankings (unplaced), then placed at position 2.
    new_id = _make_movie(test_client, imdb='tt7999', title='Inserted')
    test_client.post(
        f"/v1/users/me/movies/{new_id}",
        headers=user_headers,
        json={'on_rankings': True},
    )
    resp = test_client.put(
        f"/v1/users/me/movies/{new_id}/rank",
        headers=user_headers,
        json={'position': 2},
    )
    assert resp.status_code == 200
    assert resp.json()['rank'] == 2

    listing = test_client.get('/v1/users/me/movies', headers=user_headers).json()
    ranked = sorted(
        [m for m in listing if m['rank'] is not None], key=lambda m: m['rank']
    )
    order = [(m['rank'], m['movie']['id']) for m in ranked]
    # ids[0]=1, inserted=2, ids[1]=3, ids[2]=4
    assert order == [(1, ids[0]), (2, new_id), (3, ids[1]), (4, ids[2])]


def test_lists_are_independent(test_client: TestClient):
    movie_id = _make_movie(test_client)
    user_headers = {'Authorization': f"Bearer {test_client.first_user.token}"}

    # Add to watchlist only.
    r = test_client.post(
        f"/v1/users/me/movies/{movie_id}",
        headers=user_headers,
        json={'on_watchlist': True},
    )
    assert r.json()['on_watchlist'] is True
    assert r.json()['on_rankings'] is False
    assert r.json()['rank'] is None

    # Also add to rankings (idempotent merge) -> now on both.
    r = test_client.post(
        f"/v1/users/me/movies/{movie_id}",
        headers=user_headers,
        json={'on_rankings': True},
    )
    assert r.json()['on_watchlist'] is True
    assert r.json()['on_rankings'] is True
    assert r.json()['rank'] is None  # unplaced until positioned

    # Remove from rankings -> still on watchlist, rank cleared.
    r = test_client.put(
        f"/v1/users/me/movies/{movie_id}",
        headers=user_headers,
        json={'on_rankings': False},
    )
    assert r.json()['on_watchlist'] is True
    assert r.json()['on_rankings'] is False
    assert r.json()['rank'] is None

    # Remove from watchlist too -> tracker deleted, gone from the list.
    test_client.put(
        f"/v1/users/me/movies/{movie_id}",
        headers=user_headers,
        json={'on_watchlist': False},
    )
    listing = test_client.get('/v1/users/me/movies', headers=user_headers).json()
    assert all(m['movie']['id'] != movie_id for m in listing)


def test_reorder_rankings(test_client: TestClient):
    user_headers = {'Authorization': f"Bearer {test_client.first_user.token}"}
    ids = []
    for i in range(3):
        mid = _make_movie(test_client, imdb=f"tt900{i}", title=f"Movie {i}")
        test_client.post(
            f"/v1/users/me/movies/{mid}",
            headers=user_headers,
            json={'on_rankings': True},
        )
        ids.append(mid)

    # Reverse the order.
    reordered = list(reversed(ids))
    resp = test_client.put(
        '/v1/users/me/movies/rankings/order',
        headers=user_headers,
        json={'movie_ids': reordered},
    )
    assert resp.status_code == 200
    data = resp.json()
    ordered_ids = [m['movie']['id'] for m in data]
    assert ordered_ids == reordered
    assert [m['rank'] for m in data] == [1, 2, 3]


def test_get_user_movies(test_client: TestClient):
    movie_id = _make_movie(test_client)
    user_headers = {'Authorization': f"Bearer {test_client.first_user.token}"}
    test_client.post(
        f"/v1/users/me/movies/{movie_id}",
        headers=user_headers,
        json={'on_rankings': True},
    )

    response = test_client.get('/v1/users/me/movies', headers=user_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert data[0]['on_rankings'] is True


def test_create_movie_unauthenticated(test_client: TestClient):
    response = test_client.post(
        '/v1/movies', json={'title': 'Inception', 'imdb': 'tt1375666'}
    )
    assert response.status_code == 401


def test_create_movie_requires_admin(test_client: TestClient):
    user_token = test_client.first_user.token
    headers = {'Authorization': f"Bearer {user_token}"}
    response = test_client.post(
        '/v1/movies', headers=headers, json={'title': 'Inception', 'imdb': 'tt1375666'}
    )
    assert response.status_code == 403


def test_update_movie_requires_admin(test_client: TestClient):
    admin_token = test_client.admin_user.token
    admin_headers = {'Authorization': f"Bearer {admin_token}"}
    created = test_client.post(
        '/v1/movies',
        headers=admin_headers,
        json={'title': 'Inception', 'imdb': 'tt1375666'},
    )
    movie_id = created.json()['id']

    user_token = test_client.first_user.token
    user_headers = {'Authorization': f"Bearer {user_token}"}
    response = test_client.put(
        f"/v1/movies/{movie_id}", headers=user_headers, json={'title': 'Hacked'}
    )
    assert response.status_code == 403


def test_search_movies_requires_auth(test_client: TestClient):
    response = test_client.get('/v1/movies/search?q=matrix')
    assert response.status_code == 401


@patch('app.services.movie_search.get_settings')
def test_search_movies_not_configured(mock_settings, test_client: TestClient):
    mock_settings.return_value = Settings(omdb_api_key=None, env='github')
    user_headers = {'Authorization': f"Bearer {test_client.first_user.token}"}
    response = test_client.get('/v1/movies/search?q=matrix', headers=user_headers)
    assert response.status_code == 503


@patch('app.services.movie_search.get_settings')
@patch('app.services.movie_search.requests.get')
def test_search_movies_returns_results(
    mock_get, mock_settings, test_client: TestClient
):
    mock_settings.return_value = Settings(omdb_api_key='test-key', env='github')
    mock_response = MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.json.return_value = {
        'Response': 'True',
        'Search': [
            {
                'Title': 'The Matrix',
                'Year': '1999',
                'imdbID': 'tt0133093',
                'Type': 'movie',
                'Poster': 'https://example.com/matrix.jpg',
            },
            {
                'Title': 'The Matrix Reloaded',
                'Year': '2003',
                'imdbID': 'tt0234215',
                'Type': 'movie',
                'Poster': 'N/A',
            },
        ],
    }
    mock_get.return_value = mock_response

    user_headers = {'Authorization': f"Bearer {test_client.first_user.token}"}
    response = test_client.get('/v1/movies/search?q=matrix', headers=user_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]['imdb'] == 'tt0133093'
    assert data[0]['title'] == 'The Matrix'
    assert data[0]['poster_url'] == 'https://example.com/matrix.jpg'
    # 'N/A' posters are normalized to null.
    assert data[1]['poster_url'] is None
