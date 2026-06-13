import pytest
from fastapi.testclient import TestClient


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
