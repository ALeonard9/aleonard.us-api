"""
Book search proxy.

Wraps the Open Library API (https://openlibrary.org — free, no key) so the
web and MCP frontends can look up books by title/author without talking to
Open Library directly. Results are normalized into the shape the
``/v1/books`` create endpoint expects. Open Library is also the enrichment
source, keyed on the catalog's ``isbn``: authors, publish year, subjects,
description (from the work record), page count, rating, and cover image.
(The legacy ``googleid`` column is retained but dormant — Google Books now
requires an API key for every request.)
"""

import re
from typing import List, Optional

import requests
from fastapi import HTTPException, status

from app.log.logging_config import logger

OPENLIBRARY_URL = 'https://openlibrary.org'
COVERS_URL = 'https://covers.openlibrary.org'
REQUEST_TIMEOUT = 10

_SEARCH_FIELDS = (
    'key,title,author_name,first_publish_year,isbn,cover_i,'
    'number_of_pages_median,subject,ratings_average,language'
)


def _cover(cover_i: Optional[int]) -> Optional[str]:
    return f'{COVERS_URL}/b/id/{cover_i}-L.jpg' if cover_i else None


def _authors(doc: dict) -> Optional[str]:
    authors = doc.get('author_name') or []
    return ', '.join(authors) if authors else None


def _pick_isbn(doc: dict) -> Optional[str]:
    """Prefer an ISBN-13 from the doc's (unordered) isbn list."""
    isbns = doc.get('isbn') or []
    for isbn in isbns:
        if len(isbn) == 13:
            return isbn
    return isbns[0] if isbns else None


def _genre(doc: dict) -> Optional[str]:
    subjects = doc.get('subject') or []
    return ', '.join(subjects[:3]) if subjects else None


def search_books(query: str) -> List[dict]:
    """
    Search Open Library for books matching ``query``.

    Returns a list of normalized dicts (``isbn``, ``title``, ``authors``,
    ``year``, ``poster_url``). Raises 400 on an empty query and 502 when the
    upstream call fails.
    """
    query = (query or '').strip()
    if not query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Search query must not be empty',
        )

    try:
        response = requests.get(
            f'{OPENLIBRARY_URL}/search.json',
            params={'q': query, 'limit': 20, 'fields': _SEARCH_FIELDS},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError) as exc:
        logger.error('Open Library search failed for %r: %s', query, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail='Upstream book search failed',
        ) from exc

    results = []
    for doc in payload.get('docs') or []:
        year = doc.get('first_publish_year')
        results.append(
            {
                'isbn': _pick_isbn(doc),
                'title': doc.get('title'),
                'authors': _authors(doc),
                'year': str(year) if year else None,
                'poster_url': _cover(doc.get('cover_i')),
            }
        )
    return results


# Max lengths for the bounded catalog columns (see models_sandbox.DbBook).
_FIELD_LIMITS = {
    'title': 254,
    'isbn': 20,
    'poster_url': 254,
    'authors': 512,
    'genre': 255,
    'language': 40,
}


def apply_detail_to_book(book, detail: dict) -> None:
    """
    Copy Open Library detail onto a DbBook, truncating to column limits and
    skipping None values (never clobber a good value with None).
    """
    for key, value in detail.items():
        if value is None:
            continue
        if key in _FIELD_LIMITS and isinstance(value, str):
            value = value[: _FIELD_LIMITS[key]]
        setattr(book, key, value)


# Open Library work keys look like "/works/OL45883W". Anything else from the
# search response is discarded before it can reach a URL (SSRF hardening).
_WORK_KEY_RE = re.compile(r'^/works/OL\d+W$')


def _work_description(work_key: Optional[str]) -> Optional[str]:
    """Fetch the work record for its description (best effort)."""
    if not work_key or not _WORK_KEY_RE.match(work_key):
        return None
    try:
        response = requests.get(
            f'{OPENLIBRARY_URL}{work_key}.json', timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        description = response.json().get('description')
    except (requests.RequestException, ValueError) as exc:
        logger.warning('Open Library work fetch failed for %s: %s', work_key, exc)
        return None
    if isinstance(description, dict):
        description = description.get('value')
    return description or None


def get_book_detail(isbn: Optional[str]) -> Optional[dict]:
    """
    Fetch full detail for a book by ISBN and map it to the fields the
    catalog stores. Returns None when unavailable so callers can skip
    enrichment gracefully.
    """
    isbn = (isbn or '').strip().replace('-', '')
    if not isbn:
        return None
    try:
        response = requests.get(
            f'{OPENLIBRARY_URL}/search.json',
            params={'q': f'isbn:{isbn}', 'limit': 1, 'fields': _SEARCH_FIELDS},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        docs = response.json().get('docs') or []
    except (requests.RequestException, ValueError) as exc:
        logger.warning('Open Library detail failed for %s: %s', isbn, exc)
        return None
    if not docs:
        return None

    doc = docs[0]
    year = doc.get('first_publish_year')
    rating = doc.get('ratings_average')
    languages = doc.get('language') or []
    return {
        'title': doc.get('title'),
        'isbn': isbn,
        'authors': _authors(doc),
        'year': year,
        'genre': _genre(doc),
        'description': _work_description(doc.get('key')),
        'page_count': doc.get('number_of_pages_median'),
        'rating': round(rating, 2) if rating else None,
        'language': languages[0] if languages else None,
        'poster_url': _cover(doc.get('cover_i')),
    }
