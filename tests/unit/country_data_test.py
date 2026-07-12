# pylint: disable=missing-module-docstring, missing-function-docstring
# pylint: disable=protected-access, missing-class-docstring
from unittest.mock import MagicMock, patch

from app.services import country_data


def test_normalize_maps_fields():
    record = {
        'name': {'common': 'Japan'},
        'cca2': 'JP',
        'region': 'Asia',
        'subregion': 'Eastern Asia',
        'capital': ['Tokyo'],
        'flag': '🇯🇵',
    }
    out = country_data._normalize(record)
    assert out['title'] == 'Japan'
    assert out['country_code'] == 'jp'  # lowercased to match the legacy catalog
    assert out['region'] == 'Asia'
    assert out['capital'] == 'Tokyo'
    assert out['flag_emoji'] == '🇯🇵'
    assert out['flag_url'] == 'https://flagcdn.com/jp.svg'


def test_normalize_handles_missing_fields():
    out = country_data._normalize({})
    assert out['title'] is None
    assert out['country_code'] is None
    assert out['capital'] is None
    assert out['flag_url'] is None


def test_apply_detail_never_renames_existing():
    class Country:
        title = 'United States'
        country_code = 'us'
        region = None

    c = Country()
    country_data.apply_detail_to_country(
        c,
        {
            'title': 'United States of America',
            'country_code': 'us',
            'region': 'Americas',
        },
    )
    assert c.title == 'United States'  # legacy title is canonical
    assert c.region == 'Americas'


@patch('app.services.country_data.requests.get')
def test_fetch_all_countries_caches_and_filters(mock_get):
    country_data._world_cache = None
    resp = MagicMock()
    resp.raise_for_status.return_value = None
    resp.json.return_value = [
        {'name': {'common': 'Japan'}, 'cca2': 'JP', 'flag': '🇯🇵'},
        {'name': {'common': 'No Code'}},  # dropped: no cca2
    ]
    mock_get.return_value = resp

    out = country_data.fetch_all_countries()
    assert len(out) == 1
    assert out[0]['country_code'] == 'jp'

    # Second call served from the module cache — no new HTTP request.
    country_data.fetch_all_countries()
    assert mock_get.call_count == 1

    detail = country_data.get_country_detail('JP')
    assert detail['title'] == 'Japan'
    assert country_data.get_country_detail('xx') is None
    assert country_data.get_country_detail(None) is None
    country_data._world_cache = None


@patch('app.services.country_data.requests.get')
def test_fetch_all_countries_failure_not_cached(mock_get):
    country_data._world_cache = None
    mock_get.side_effect = ValueError('boom')
    assert country_data.fetch_all_countries() == []
    # A failed fetch must not poison the cache.
    assert country_data._world_cache is None
    country_data._world_cache = None
