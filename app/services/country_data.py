"""
Country catalog data.

Sources the mledoze/countries dataset (the open dataset REST Countries was
built on — a single static JSON, no key required) for catalog enrichment:
region, subregion, capital, and flag emoji, keyed on the catalog's lowercase
ISO-2 ``country_code``. Flag images come from the flagcdn.com CDN. Also
provides the full world list so the catalog can be seeded for the travel
bucket list.

The whole dataset is one ~1.4 MB fetch, cached for the process lifetime.
"""

from typing import List, Optional

import requests

from app.log.logging_config import logger

WORLD_DATA_URL = (
    'https://raw.githubusercontent.com/mledoze/countries/master/countries.json'
)
FLAG_CDN_URL = 'https://flagcdn.com'
REQUEST_TIMEOUT = 30

_world_cache: Optional[List[dict]] = None


def _normalize(payload: dict) -> dict:
    """Map one mledoze/countries record to the catalog's fields."""
    code = (payload.get('cca2') or '').lower() or None
    capitals = payload.get('capital') or []
    return {
        'title': (payload.get('name') or {}).get('common'),
        'country_code': code,
        'region': payload.get('region') or None,
        'subregion': payload.get('subregion') or None,
        'capital': capitals[0] if capitals else None,
        'flag_emoji': payload.get('flag'),
        'flag_url': f'{FLAG_CDN_URL}/{code}.svg' if code else None,
    }


def fetch_all_countries() -> List[dict]:
    """
    Fetch the full world list, normalized to catalog fields and cached for
    the process lifetime. Returns [] when unavailable.
    """
    global _world_cache  # pylint: disable=global-statement
    if _world_cache is not None:
        return _world_cache
    try:
        response = requests.get(WORLD_DATA_URL, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError) as exc:
        logger.error('Country dataset fetch failed: %s', exc)
        return []
    normalized = [_normalize(item) for item in payload if isinstance(item, dict)]
    _world_cache = [c for c in normalized if c['country_code'] and c['title']]
    return _world_cache


def get_country_detail(country_code: Optional[str]) -> Optional[dict]:
    """
    Detail for one country by ISO-2 code, from the cached world list.
    Returns None when unavailable so callers can skip enrichment gracefully.
    """
    country_code = (country_code or '').strip().lower()
    if not country_code:
        return None
    for country in fetch_all_countries():
        if country['country_code'] == country_code:
            return country
    return None


def apply_detail_to_country(country, detail: dict) -> None:
    """
    Copy dataset detail onto a DbCountry, skipping None values and never
    renaming an existing catalog entry (legacy titles are canonical).
    """
    for key, value in detail.items():
        if value is None:
            continue
        if key == 'title' and country.title:
            continue
        if key == 'country_code' and country.country_code:
            continue
        setattr(country, key, value)


def seed_countries(db) -> int:
    """
    Upsert the full world list into the catalog, keyed on country_code.
    Existing rows are enriched in place; missing countries are created.
    Returns the number of countries created.
    """
    # Imported locally to avoid a service->models import at module load in
    # callers that only need detail lookups.
    from app.db.models_sandbox import (  # pylint: disable=import-outside-toplevel
        DbCountry,
    )

    world = fetch_all_countries()
    if not world:
        return 0

    # Key case-insensitively — legacy rows may carry uppercase codes.
    existing = {
        c.country_code.lower(): c for c in db.query(DbCountry) if c.country_code
    }
    created = 0
    for data in world:
        current = existing.get(data['country_code'])
        if current:
            apply_detail_to_country(current, data)
        else:
            db.add(DbCountry(**data))
            created += 1
    return created
