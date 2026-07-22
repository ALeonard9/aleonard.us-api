"""
The four tracked domains, described once.

Movies, TV, Books and Games have identical tracker shapes: ``on_rankings`` /
``on_watchlist`` / ``rank`` against a catalog row carrying a title, year and
poster. Endpoints that work across all four — the public profile and the home
summary — read this registry instead of repeating the tuple, so the shelf list
stays in one place.
"""

from typing import NamedTuple, Tuple, Type

from app.db.models_sandbox import (
    DbBook,
    DbMovie,
    DbTVShow,
    DbUserBook,
    DbUserMovie,
    DbUserTVShow,
    DbUserVideoGame,
    DbVideoGame,
)


class Shelf(NamedTuple):
    """One tracked domain and the bits generic queries need to reach it."""

    # URL/JSON slug ('movies'). Stable — clients key off this.
    category: str
    # Human label ('Video Games'), as it appears on profiles and share cards.
    label: str
    # Attribute on DbUser holding this shelf's public opt-in flag.
    visibility_flag: str
    tracker_model: Type
    catalog_model: Type
    # Tracker column joining to ``catalog_model.pk``.
    join_col: str


SHELVES: Tuple[Shelf, ...] = (
    Shelf('movies', 'Movies', 'public_movies', DbUserMovie, DbMovie, 'movie_id'),
    Shelf('tv', 'TV', 'public_tv', DbUserTVShow, DbTVShow, 'tv_show_id'),
    Shelf('books', 'Books', 'public_books', DbUserBook, DbBook, 'book_id'),
    Shelf(
        'games',
        'Video Games',
        'public_games',
        DbUserVideoGame,
        DbVideoGame,
        'game_id',
    ),
)
