# pylint: disable=missing-module-docstring, missing-function-docstring
import pytest
from fastapi.testclient import TestClient

from app.services.tracker_query import MAX_PAGE

# (list path, catalog path, catalog payload builder)
DOMAINS = (
    ('movies', '/v1/movies', lambda i: {'title': f'M{i}', 'imdb': f'tt50{i}'}),
    ('books', '/v1/books', lambda i: {'title': f'B{i}', 'googleid': f'gid50{i}'}),
    ('games', '/v1/games', lambda i: {'title': f'G{i}', 'igdb': 5000 + i}),
)


def _auth(token: str) -> dict:
    return {'Authorization': f'Bearer {token}'}


def _seed(test_client: TestClient, domain: str, catalog_path: str, payload, count: int):
    """Create ``count`` catalog rows; rank the odd ones, queue the even ones."""
    token = test_client.first_user.token
    for i in range(count):
        entity_id = test_client.post(
            catalog_path, headers=_auth(test_client.admin_user.token), json=payload(i)
        ).json()['id']
        test_client.post(
            f'/v1/users/me/{domain}/{entity_id}',
            headers=_auth(token),
            json=({'on_rankings': True} if i % 2 else {'on_watchlist': True}),
        )


@pytest.mark.parametrize('domain,catalog_path,payload', DOMAINS)
def test_limit_and_offset_page_the_list(
    test_client: TestClient, domain, catalog_path, payload
):
    token = test_client.first_user.token
    _seed(test_client, domain, catalog_path, payload, 6)
    path = f'/v1/users/me/{domain}'

    assert len(test_client.get(path, headers=_auth(token)).json()) == 6
    assert len(test_client.get(f'{path}?limit=2', headers=_auth(token)).json()) == 2
    assert (
        len(test_client.get(f'{path}?limit=10&offset=4', headers=_auth(token)).json())
        == 2
    )


@pytest.mark.parametrize('domain,catalog_path,payload', DOMAINS)
def test_list_filters(test_client: TestClient, domain, catalog_path, payload):
    token = test_client.first_user.token
    _seed(test_client, domain, catalog_path, payload, 6)
    path = f'/v1/users/me/{domain}'

    ranked = test_client.get(f'{path}?on_rankings=true', headers=_auth(token)).json()
    queued = test_client.get(f'{path}?on_watchlist=true', headers=_auth(token)).json()
    assert len(ranked) == 3
    assert len(queued) == 3
    assert all(r['on_rankings'] for r in ranked)
    assert all(q['on_watchlist'] for q in queued)


def test_limit_is_capped_at_max_page(test_client: TestClient):
    response = test_client.get(
        f'/v1/users/me/movies?limit={MAX_PAGE + 1}',
        headers=_auth(test_client.first_user.token),
    )
    assert response.status_code == 422


def test_tv_list_takes_the_same_params(test_client: TestClient):
    token = test_client.first_user.token
    show_id = test_client.post(
        '/v1/tv-shows',
        headers=_auth(test_client.admin_user.token),
        json={'title': 'Show', 'tvmaze': 5001},
    ).json()['id']
    test_client.post(
        f'/v1/users/me/tv-shows/{show_id}',
        headers=_auth(token),
        json={'on_watchlist': True},
    )

    assert (
        len(
            test_client.get(
                '/v1/users/me/tv-shows?on_watchlist=true', headers=_auth(token)
            ).json()
        )
        == 1
    )
    assert (
        test_client.get(
            '/v1/users/me/tv-shows?on_rankings=true', headers=_auth(token)
        ).json()
        == []
    )
