"""
Test API-key management and key-based authentication.
"""

from fastapi.testclient import TestClient


def _create_key(test_client: TestClient, token: str, name: str = 'laptop mcp'):
    return test_client.post(
        '/v1/users/me/api-keys',
        json={'name': name},
        headers={'Authorization': f'Bearer {token}'},
    )


def test_create_key_returns_secret_once(test_client: TestClient):
    '''
    Creation returns the plaintext once; listings never do.
    '''
    response = _create_key(test_client, test_client.first_user.token)
    assert response.status_code == 201
    body = response.json()
    assert body['name'] == 'laptop mcp'
    assert body['key'].startswith('drk_')
    assert body['prefix'] == body['key'][:12]
    # Listings never expose the secret
    listing = test_client.get(
        '/v1/users/me/api-keys',
        headers={'Authorization': f'Bearer {test_client.first_user.token}'},
    )
    assert listing.status_code == 200
    assert len(listing.json()) == 1
    assert 'key' not in listing.json()[0]
    assert listing.json()[0]['prefix'] == body['prefix']


def test_api_key_authenticates_as_owner(test_client: TestClient):
    '''
    A drk_ bearer token resolves to its owner and stamps last_used_at.
    '''
    key = _create_key(test_client, test_client.first_user.token).json()['key']
    response = test_client.get(
        '/v1/users/me/api-keys', headers={'Authorization': f'Bearer {key}'}
    )
    assert response.status_code == 200
    assert response.json()[0]['name'] == 'laptop mcp'
    # last_used_at is stamped by the auth path
    assert response.json()[0]['last_used_at'] is not None


def test_bogus_api_key_rejected(test_client: TestClient):
    '''
    Unknown keys get a 401.
    '''
    response = test_client.get(
        '/v1/users/me/api-keys',
        headers={'Authorization': 'Bearer drk_' + '0' * 48},
    )
    assert response.status_code == 401


def test_revoked_key_stops_working(test_client: TestClient):
    '''
    Deleting a key immediately kills its auth.
    '''
    token = test_client.first_user.token
    created = _create_key(test_client, token).json()
    revoke = test_client.delete(
        f"/v1/users/me/api-keys/{created['id']}",
        headers={'Authorization': f'Bearer {token}'},
    )
    assert revoke.status_code == 204
    response = test_client.get(
        '/v1/users/me/api-keys',
        headers={'Authorization': f"Bearer {created['key']}"},
    )
    assert response.status_code == 401


def test_cannot_revoke_another_users_key(test_client: TestClient):
    '''
    Users can't see or revoke each other's keys.
    '''
    created = _create_key(test_client, test_client.first_user.token).json()
    response = test_client.delete(
        f"/v1/users/me/api-keys/{created['id']}",
        headers={'Authorization': f'Bearer {test_client.second_user.token}'},
    )
    assert response.status_code == 404
    # Still works for the owner
    listing = test_client.get(
        '/v1/users/me/api-keys',
        headers={'Authorization': f"Bearer {created['key']}"},
    )
    assert listing.status_code == 200
