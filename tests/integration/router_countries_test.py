import pytest
from fastapi.testclient import TestClient


def test_create_country(test_client: TestClient):
    admin_token = test_client.admin_user.token
    headers = {'Authorization': f"Bearer {admin_token}"}
    response = test_client.post(
        '/v1/countries', headers=headers, json={'title': 'Japan', 'country_code': 'JP'}
    )
    assert response.status_code == 201
    data = response.json()
    assert data['title'] == 'Japan'
    assert data['country_code'] == 'JP'


def test_get_countries(test_client: TestClient):
    admin_token = test_client.admin_user.token
    headers = {'Authorization': f"Bearer {admin_token}"}
    test_client.post(
        '/v1/countries', headers=headers, json={'title': 'Japan', 'country_code': 'JP'}
    )

    response = test_client.get('/v1/countries')
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0


def test_mark_country_visited(test_client: TestClient):
    admin_token = test_client.admin_user.token
    headers = {'Authorization': f"Bearer {admin_token}"}

    response = test_client.post(
        '/v1/countries', headers=headers, json={'title': 'Japan', 'country_code': 'JP'}
    )
    country_id = response.json()['id']

    user_token = test_client.first_user.token
    user_headers = {'Authorization': f"Bearer {user_token}"}

    response = test_client.post(
        f"/v1/users/me/countries/{country_id}",
        headers=user_headers,
        json={'rank': 1, 'notes': 'Beautiful country!'},
    )
    assert response.status_code == 201
    data = response.json()
    assert data['rank'] == 1
    assert data['notes'] == 'Beautiful country!'


def test_get_user_countries(test_client: TestClient):
    admin_token = test_client.admin_user.token
    headers = {'Authorization': f"Bearer {admin_token}"}

    response = test_client.post(
        '/v1/countries', headers=headers, json={'title': 'Japan', 'country_code': 'JP'}
    )
    country_id = response.json()['id']

    user_token = test_client.first_user.token
    user_headers = {'Authorization': f"Bearer {user_token}"}
    test_client.post(
        f"/v1/users/me/countries/{country_id}", headers=user_headers, json={'rank': 1}
    )

    response = test_client.get('/v1/users/me/countries', headers=user_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert data[0]['rank'] == 1
