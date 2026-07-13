"""
Movie search proxy.

Wraps the OMDB search API (mirroring the legacy ``movies/findmovie.php``) so the
web and MCP frontends can look up movies by title without holding the API key.
Results are normalized into the shape the ``/v1/movies`` create endpoint expects.
"""

from typing import List, Optional

import requests
from fastapi import HTTPException, status

from app.config import get_settings
from app.log.logging_config import logger

OMDB_URL = 'https://www.omdbapi.com/'
REQUEST_TIMEOUT = 10


def search_movies(query: str) -> List[dict]:
    """
    Search OMDB for movies matching ``query``.

    Returns a list of normalized dicts (``imdb``, ``title``, ``year``,
    ``poster_url``, ``type``). Raises 503 when the API key is not configured
    and 502 when the upstream call fails.
    """
    query = (query or '').strip()
    if not query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Search query must not be empty',
        )

    settings = get_settings()
    if not settings.omdb_api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail='Movie search is not configured (OMDB_API_KEY missing)',
        )

    try:
        response = requests.get(
            OMDB_URL,
            params={
                'apikey': settings.omdb_api_key,
                's': query,
                'type': 'movie',
            },
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.error('OMDB search failed for %r: %s', query, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail='Upstream movie search failed',
        ) from exc

    payload = response.json()
    if payload.get('Response') == 'False':
        # OMDB reports "Movie not found!" etc. as a non-error empty result.
        return []

    results = []
    for item in payload.get('Search', []):
        poster = item.get('Poster')
        if poster in (None, 'N/A'):
            poster = None
        results.append(
            {
                'imdb': item.get('imdbID'),
                'title': item.get('Title'),
                'year': item.get('Year'),
                'poster_url': poster,
                'type': item.get('Type'),
            }
        )
    return results


def _na(value):
    """Normalize OMDB's 'N/A' / empty strings to None."""
    if value in (None, '', 'N/A'):
        return None
    return value


def _to_int(value):
    """Parse a leading integer (e.g. year '2002', runtime '113 min')."""
    value = _na(value)
    if value is None:
        return None
    digits = ''
    for ch in str(value):
        if ch.isdigit():
            digits += ch
        elif digits:
            break
    return int(digits) if digits else None


def _to_float(value):
    value = _na(value)
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


# Max lengths for the bounded catalog columns (see models_sandbox.DbMovie).
_FIELD_LIMITS = {
    'title': 255,
    'director': 512,
    'genre': 255,
    'language': 40,
    'rated': 11,
    'poster_url': 500,
}


def apply_detail_to_movie(movie, detail: dict) -> None:
    """
    Copy OMDB detail onto a DbMovie, truncating to column limits and only
    filling empty fields (never clobber a good value with None).
    """
    for key, value in detail.items():
        if value is None:
            continue
        if key in _FIELD_LIMITS and isinstance(value, str):
            value = value[: _FIELD_LIMITS[key]]
        setattr(movie, key, value)


def get_movie_detail(imdb_id: str) -> Optional[dict]:
    """
    Fetch full detail for a movie by imdb id (OMDB ``i=``) and map it to the
    fields the catalog stores. Returns None when unavailable/unconfigured so
    callers can skip enrichment gracefully.
    """
    imdb_id = (imdb_id or '').strip()
    if not imdb_id:
        return None
    settings = get_settings()
    if not settings.omdb_api_key:
        return None
    try:
        response = requests.get(
            OMDB_URL,
            params={'apikey': settings.omdb_api_key, 'i': imdb_id, 'plot': 'full'},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError) as exc:
        logger.warning('OMDB detail failed for %s: %s', imdb_id, exc)
        return None
    if payload.get('Response') == 'False':
        return None

    return {
        'title': _na(payload.get('Title')),
        'imdb': imdb_id,
        'year': _to_int(payload.get('Year')),
        'runtime': _to_int(payload.get('Runtime')),
        'rated': _na(payload.get('Rated')),
        'genre': _na(payload.get('Genre')),
        'director': _na(payload.get('Director')),
        'actors': _na(payload.get('Actors')),
        'plot': _na(payload.get('Plot')),
        'language': _na(payload.get('Language')),
        'rating_imdb': _to_float(payload.get('imdbRating')),
        'poster_url': _na(payload.get('Poster')),
    }
