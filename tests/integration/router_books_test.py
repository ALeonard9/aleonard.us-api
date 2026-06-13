import pytest
from fastapi.testclient import TestClient


def test_create_book(test_client: TestClient):
    admin_token = test_client.admin_user.token
    headers = {'Authorization': f"Bearer {admin_token}"}
    response = test_client.post(
        '/v1/books', headers=headers, json={'title': 'Dune', 'isbn': '978-0441172719'}
    )
    assert response.status_code == 201
    data = response.json()
    assert data['title'] == 'Dune'
    assert data['isbn'] == '978-0441172719'


def test_mark_book(test_client: TestClient):
    admin_token = test_client.admin_user.token
    headers = {'Authorization': f"Bearer {admin_token}"}

    response = test_client.post(
        '/v1/books', headers=headers, json={'title': 'Dune', 'isbn': '978-0441172719'}
    )
    book_id = response.json()['id']

    user_token = test_client.first_user.token
    user_headers = {'Authorization': f"Bearer {user_token}"}

    response = test_client.post(
        f"/v1/users/me/books/{book_id}",
        headers=user_headers,
        json={'rank': 2, 'notes': 'A masterpiece.'},
    )
    assert response.status_code == 201
    data = response.json()
    assert data['rank'] == 2
    assert data['notes'] == 'A masterpiece.'
