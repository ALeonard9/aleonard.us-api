"""
Search-result ranking: cap each domain's hits and surface the best match
first.

Providers already filter to items relevant to the query, but not
necessarily in an order that puts the *best* match first — searching
"Titanic" can bury the 1997 movie under lesser-known or same-named titles,
same for "Zelda" and incidental matches. We re-rank locally with a simple
tiered heuristic instead of pulling in a fuzzy-matching library:

    1. exact / near-exact title match (case- and punctuation-insensitive)
    2. title starts with the query
    3. title contains the query
    4. anything else (the provider matched on something other than the
       title, e.g. an alternate title, author, or its own fuzzy search)

Within a tier, ties are broken by each provider's own result order, which
doubles as its relevance/popularity signal (TVMaze scores its matches,
Open Library and IGDB both sort search hits by relevance by default, and
OMDB returns its closest matches first) — Python's ``sorted`` is stable, so
that order is preserved automatically. The tiered list is then capped to
``limit`` per domain so the UI shows a short, best-first list instead of a
long unranked one.
"""

import re
from typing import List

_NORMALIZE_RE = re.compile(r'[^a-z0-9]+')

DEFAULT_DOMAIN_CAP = 5

# Higher is better; see module docstring for what each tier means.
_TIER_EXACT = 3
_TIER_STARTS_WITH = 2
_TIER_CONTAINS = 1
_TIER_OTHER = 0


def _normalize(text: str) -> str:
    """Lowercase and strip everything but alphanumerics, so 'Spider-Man'
    and 'spider man' (or 'Spider Man!') compare equal."""
    return _NORMALIZE_RE.sub('', (text or '').lower())


def _tier(query: str, title: str) -> int:
    """Score how closely ``title`` matches ``query``; see module docstring."""
    q = _normalize(query)
    t = _normalize(title)
    if not q or not t:
        return _TIER_OTHER
    if q == t:
        return _TIER_EXACT
    if t.startswith(q):
        return _TIER_STARTS_WITH
    if q in t:
        return _TIER_CONTAINS
    return _TIER_OTHER


def rank_and_cap(
    query: str, results: List[dict], limit: int = DEFAULT_DOMAIN_CAP
) -> List[dict]:
    """
    Sort ``results`` best-match-first (see module docstring for the tiers)
    and truncate to ``limit``. Safe to call with an empty list.
    """
    ranked = sorted(
        results,
        key=lambda item: _tier(query, item.get('title') or ''),
        reverse=True,
    )
    return ranked[:limit]
