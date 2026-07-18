# pylint: disable=missing-module-docstring, missing-function-docstring
from fastapi.testclient import TestClient


def _auth(token: str) -> dict:
    return {'Authorization': f'Bearer {token}'}


def _seed_movie(test_client: TestClient, rank: bool):
    admin = _auth(test_client.admin_user.token)
    movie_id = test_client.post(
        '/v1/movies',
        headers=admin,
        json={'title': 'Inception', 'imdb': 'tt1375666', 'year': 2010},
    ).json()['id']
    user = _auth(test_client.first_user.token)
    test_client.post(
        f'/v1/users/me/movies/{movie_id}',
        headers=user,
        json={'on_rankings': rank, 'on_watchlist': not rank, 'notes': 'good'},
    )
    if rank:
        test_client.put(
            f'/v1/users/me/movies/{movie_id}/rank',
            headers=user,
            json={'position': 1},
        )
    return movie_id


def test_export_json_covers_domains_and_licenses(test_client: TestClient):
    _seed_movie(test_client, rank=True)
    response = test_client.get(
        '/v1/users/me/export', headers=_auth(test_client.first_user.token)
    )
    assert response.status_code == 200
    body = response.json()
    for key in (
        'exported_at',
        'account',
        'licenses',
        'movies',
        'tv_shows',
        'tv_episode_marks',
        'books',
        'games',
    ):
        assert key in body
    assert body['movies'][0]['movie']['title'] == 'Inception'
    assert body['movies'][0]['rank'] == 1
    assert body['movies'][0]['notes'] == 'good'
    assert 'CC BY-SA' in body['licenses']['tv']


def test_export_json_is_scoped_to_the_caller(test_client: TestClient):
    _seed_movie(test_client, rank=True)
    response = test_client.get(
        '/v1/users/me/export', headers=_auth(test_client.second_user.token)
    )
    assert response.status_code == 200
    assert response.json()['movies'] == []


def test_export_movies_csv(test_client: TestClient):
    _seed_movie(test_client, rank=False)
    response = test_client.get(
        '/v1/users/me/export/movies.csv',
        headers=_auth(test_client.first_user.token),
    )
    assert response.status_code == 200
    assert response.headers['content-type'].startswith('text/csv')
    assert 'druthers-movies.csv' in response.headers['content-disposition']
    lines = response.text.strip().splitlines()
    assert lines[0].startswith('title,year,state,rank')
    assert lines[1].startswith('Inception,2010,watchlist,')


def test_export_unknown_domain_404s(test_client: TestClient):
    response = test_client.get(
        '/v1/users/me/export/vibes.csv',
        headers=_auth(test_client.first_user.token),
    )
    assert response.status_code == 404


def test_export_requires_auth(test_client: TestClient):
    assert test_client.get('/v1/users/me/export').status_code == 401
