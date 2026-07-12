# pylint: disable=missing-module-docstring, missing-function-docstring
from unittest.mock import patch

from fastapi.testclient import TestClient


def _make_country(test_client: TestClient, title='Japan', code='jp') -> str:
    headers = {'Authorization': f"Bearer {test_client.admin_user.token}"}
    with patch('app.router.v1.router_countries.get_country_detail', return_value=None):
        resp = test_client.post(
            '/v1/countries',
            headers=headers,
            json={'title': title, 'country_code': code},
        )
    assert resp.status_code == 201
    return resp.json()['id']


# --- Global catalog ---
def test_create_country_normalizes_code(test_client: TestClient):
    headers = {'Authorization': f"Bearer {test_client.admin_user.token}"}
    with patch('app.router.v1.router_countries.get_country_detail', return_value=None):
        response = test_client.post(
            '/v1/countries',
            headers=headers,
            json={'title': 'Japan', 'country_code': 'JP'},
        )
    assert response.status_code == 201
    data = response.json()
    assert data['title'] == 'Japan'
    assert data['country_code'] == 'jp'


def test_get_countries(test_client: TestClient):
    _make_country(test_client)
    response = test_client.get('/v1/countries')
    assert response.status_code == 200
    assert len(response.json()) > 0


def test_create_country_requires_admin(test_client: TestClient):
    headers = {'Authorization': f"Bearer {test_client.first_user.token}"}
    response = test_client.post(
        '/v1/countries', headers=headers, json={'title': 'Japan', 'country_code': 'jp'}
    )
    assert response.status_code == 403


def test_create_duplicate_code_rejected(test_client: TestClient):
    _make_country(test_client, code='jp')
    headers = {'Authorization': f"Bearer {test_client.admin_user.token}"}
    with patch('app.router.v1.router_countries.get_country_detail', return_value=None):
        dup = test_client.post(
            '/v1/countries',
            headers=headers,
            json={'title': 'Japan again', 'country_code': 'JP'},
        )
    assert dup.status_code == 400


@patch('app.router.v1.router_countries.get_country_detail')
def test_get_country_enriches_on_view(mock_detail, test_client: TestClient):
    country_id = _make_country(test_client)
    mock_detail.return_value = {
        'region': 'Asia',
        'subregion': 'Eastern Asia',
        'capital': 'Tokyo',
        'population': 125000000,
        'flag_emoji': '🇯🇵',
        'flag_url': 'https://flagcdn.com/jp.svg',
    }
    headers = {'Authorization': f"Bearer {test_client.first_user.token}"}
    resp = test_client.get(f"/v1/countries/{country_id}", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data['region'] == 'Asia'
    assert data['capital'] == 'Tokyo'
    assert data['flag_emoji'] == '🇯🇵'


@patch('app.router.v1.router_countries.seed_countries')
def test_sync_countries_requires_admin(mock_seed, test_client: TestClient):
    headers = {'Authorization': f"Bearer {test_client.first_user.token}"}
    resp = test_client.post('/v1/countries/sync', headers=headers)
    assert resp.status_code == 403
    mock_seed.assert_not_called()

    admin_headers = {'Authorization': f"Bearer {test_client.admin_user.token}"}
    mock_seed.return_value = 0
    resp = test_client.post('/v1/countries/sync', headers=admin_headers)
    assert resp.status_code == 200
    mock_seed.assert_called_once()


# --- Trackers (bucket list + visited rankings) ---
def test_mark_country_bucket_list(test_client: TestClient):
    country_id = _make_country(test_client)
    headers = {'Authorization': f"Bearer {test_client.first_user.token}"}
    response = test_client.post(
        f"/v1/users/me/countries/{country_id}",
        headers=headers,
        json={'on_watchlist': True, 'notes': 'Cherry blossom season.'},
    )
    assert response.status_code == 201
    data = response.json()
    assert data['on_watchlist'] is True
    assert data['on_rankings'] is False
    assert data['rank'] is None


def test_mark_country_visited_with_date(test_client: TestClient):
    country_id = _make_country(test_client)
    headers = {'Authorization': f"Bearer {test_client.first_user.token}"}
    response = test_client.post(
        f"/v1/users/me/countries/{country_id}",
        headers=headers,
        json={'on_rankings': True, 'first_visited': '2019-04-02T00:00:00'},
    )
    assert response.status_code == 201
    data = response.json()
    assert data['on_rankings'] is True
    assert data['rank'] is None  # unplaced until positioned
    assert data['first_visited'].startswith('2019-04-02')


def test_set_country_rank_inserts_and_shifts(test_client: TestClient):
    headers = {'Authorization': f"Bearer {test_client.first_user.token}"}
    codes = ['jp', 'ca', 'nl']
    ids = []
    for i, code in enumerate(codes):
        cid = _make_country(test_client, title=f"Country {i}", code=code)
        test_client.post(
            f"/v1/users/me/countries/{cid}",
            headers=headers,
            json={'on_rankings': True},
        )
        ids.append(cid)
    test_client.put(
        '/v1/users/me/countries/rankings/order',
        headers=headers,
        json={'country_ids': ids},
    )

    new_id = _make_country(test_client, title='Inserted', code='sg')
    test_client.post(
        f"/v1/users/me/countries/{new_id}", headers=headers, json={'on_rankings': True}
    )
    resp = test_client.put(
        f"/v1/users/me/countries/{new_id}/rank", headers=headers, json={'position': 2}
    )
    assert resp.status_code == 200
    assert resp.json()['rank'] == 2

    listing = test_client.get('/v1/users/me/countries', headers=headers).json()
    ranked = sorted(
        [t for t in listing if t['rank'] is not None], key=lambda t: t['rank']
    )
    order = [(t['rank'], t['country']['id']) for t in ranked]
    assert order == [(1, ids[0]), (2, new_id), (3, ids[1]), (4, ids[2])]


def test_bucket_to_visited_transition(test_client: TestClient):
    """Moving a country from the bucket list to visited keeps one tracker."""
    country_id = _make_country(test_client)
    headers = {'Authorization': f"Bearer {test_client.first_user.token}"}
    test_client.post(
        f"/v1/users/me/countries/{country_id}",
        headers=headers,
        json={'on_watchlist': True},
    )
    r = test_client.post(
        f"/v1/users/me/countries/{country_id}",
        headers=headers,
        json={
            'on_watchlist': False,
            'on_rankings': True,
            'first_visited': '2026-07-01T00:00:00',
        },
    )
    assert r.json()['on_watchlist'] is False
    assert r.json()['on_rankings'] is True

    listing = test_client.get('/v1/users/me/countries', headers=headers).json()
    matches = [t for t in listing if t['country']['id'] == country_id]
    assert len(matches) == 1


def test_get_user_countries(test_client: TestClient):
    country_id = _make_country(test_client)
    headers = {'Authorization': f"Bearer {test_client.first_user.token}"}
    test_client.post(
        f"/v1/users/me/countries/{country_id}",
        headers=headers,
        json={'on_rankings': True},
    )
    response = test_client.get('/v1/users/me/countries', headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert data[0]['on_rankings'] is True
