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


def test_mark_movie(test_client: TestClient):
    admin_token = test_client.admin_user.token
    headers = {'Authorization': f"Bearer {admin_token}"}

    response = test_client.post(
        '/v1/movies', headers=headers, json={'title': 'Inception', 'imdb': 'tt1375666'}
    )
    movie_id = response.json()['id']

    user_token = test_client.first_user.token
    user_headers = {'Authorization': f"Bearer {user_token}"}

    response = test_client.post(
        f"/v1/users/me/movies/{movie_id}",
        headers=user_headers,
        json={'rank': 1, 'notes': 'Mind-bending!'},
    )
    assert response.status_code == 201
    data = response.json()
    assert data['rank'] == 1
    assert data['notes'] == 'Mind-bending!'


def test_get_user_movies(test_client: TestClient):
    admin_token = test_client.admin_user.token
    headers = {'Authorization': f"Bearer {admin_token}"}

    response = test_client.post(
        '/v1/movies', headers=headers, json={'title': 'Inception', 'imdb': 'tt1375666'}
    )
    movie_id = response.json()['id']

    user_token = test_client.first_user.token
    user_headers = {'Authorization': f"Bearer {user_token}"}
    test_client.post(
        f"/v1/users/me/movies/{movie_id}", headers=user_headers, json={'rank': 1}
    )

    response = test_client.get('/v1/users/me/movies', headers=user_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert data[0]['rank'] == 1


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
