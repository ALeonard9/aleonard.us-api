"""
Movie search proxy.

Wraps the OMDB search API (mirroring the legacy ``movies/findmovie.php``) so the
web and MCP frontends can look up movies by title without holding the API key.
Results are normalized into the shape the ``/v1/movies`` create endpoint expects.
"""

from typing import List

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
