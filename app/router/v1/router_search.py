# pylint: disable=missing-function-docstring
"""
Global cross-domain search: one query fanned out to every provider.

Providers are independent external APIs, so they run in parallel; a provider
failing (or being unconfigured) yields an empty list for its domain rather
than failing the whole search. Domains that come back empty are retried once
with a spelling correction — some providers fuzzy-match and some don't.
"""

from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.oauth2 import get_current_user
from app.db.database import get_db
from app.schemas.schemas_sandbox import GlobalSearchResponse
from app.services.rate_limit import search_rate_limit
from app.services.book_search import search_books
from app.services.game_search import search_games
from app.services.movie_search import search_movies
from app.services.search_correction import correct_query
from app.services.tracked_status import attach_tracked_status
from app.services.tv_search import search_tv_shows

router = APIRouter(prefix='/v1', tags=['Search'])


def _providers() -> Dict[str, Callable[[str], List[dict]]]:
    # Resolved at call time (not module load) so tests can patch the
    # module-level search functions.
    return {
        'movies': search_movies,
        'tv_shows': search_tv_shows,
        'games': search_games,
        'books': search_books,
    }


def _fan_out(q: str, only: Optional[List[str]] = None) -> Dict[str, List[dict]]:
    def run(fn: Callable[[str], List[dict]]) -> List[dict]:
        try:
            return fn(q)
        except HTTPException:
            # Unconfigured/unavailable provider: skip its domain, keep the rest.
            return []

    providers = _providers()
    if only is not None:
        providers = {name: fn for name, fn in providers.items() if name in only}
    with ThreadPoolExecutor(max_workers=max(len(providers), 1)) as pool:
        futures = {name: pool.submit(run, fn) for name, fn in providers.items()}
        return {name: future.result() for name, future in futures.items()}


@router.get(
    '/search',
    response_model=GlobalSearchResponse,
    dependencies=[Depends(search_rate_limit)],
)
def global_search(
    q: str,
    db: Session = Depends(get_db),
    current_user: list = Depends(get_current_user),
):
    results = _fan_out(q)
    corrected = None
    # Some providers fuzzy-match and some don't, so retry only the domains
    # that came back empty with a spell-corrected query.
    empty = [name for name, hits in results.items() if not hits]
    if empty:
        respelled = correct_query(q)
        if respelled:
            retried = _fan_out(respelled, only=empty)
            if any(retried.values()):
                corrected = respelled
                results.update(retried)
    user_pk = current_user[0].pk
    for domain, hits in results.items():
        attach_tracked_status(db, user_pk, hits, domain)
    return GlobalSearchResponse(query=q, corrected=corrected, **results)
