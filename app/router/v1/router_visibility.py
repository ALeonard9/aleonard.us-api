# pylint: disable=missing-function-docstring
"""
Visibility settings (#143) and the public read-only profile.

Everything is private by default. A user opts categories in one by one and
claims a handle; the public endpoint then serves *ranked lists only* — no
notes, no watchlist, no watch state, no activity.
"""

import re

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.oauth2 import get_current_user
from app.db.database import get_db
from app.db.models import DbUser
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
from app.schemas.model_schemas import InVisibilityUpdate, OutVisibility

router = APIRouter(prefix='/v1', tags=['Visibility'])

HANDLE_RE = re.compile(r'^[a-z0-9][a-z0-9-]{2,29}$')
# Namespace words a profile handle must never shadow.
RESERVED_HANDLES = {
    'about',
    'admin',
    'api',
    'druthers',
    'login',
    'me',
    'public',
    'settings',
    'u',
    'www',
}

# (flag attribute, label, tracker model, catalog model, join column)
_SHELVES = (
    ('public_movies', 'Movies', DbUserMovie, DbMovie, 'movie_id'),
    ('public_tv', 'TV', DbUserTVShow, DbTVShow, 'tv_show_id'),
    ('public_books', 'Books', DbUserBook, DbBook, 'book_id'),
    ('public_games', 'Video Games', DbUserVideoGame, DbVideoGame, 'game_id'),
)


@router.get('/users/me/visibility', response_model=OutVisibility)
def get_visibility(current_user: list = Depends(get_current_user)):
    return current_user[0]


@router.put('/users/me/visibility', response_model=OutVisibility)
def update_visibility(
    request: InVisibilityUpdate,
    db: Session = Depends(get_db),
    current_user: list = Depends(get_current_user),
):
    """
    Update the handle and/or per-category public flags. Opening any category
    to the public requires a handle (that's the profile URL).
    """
    user = current_user[0]
    data = request.model_dump(exclude_unset=True)

    if 'handle' in data:
        handle = (data['handle'] or '').strip().lower() or None
        if handle is not None:
            if not HANDLE_RE.match(handle):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                    detail='Handle must be 3-30 chars: lowercase letters, '
                    'digits, hyphens; starting with a letter or digit',
                )
            if handle in RESERVED_HANDLES:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail='That handle is reserved',
                )
            taken = (
                db.query(DbUser)
                .filter(DbUser.handle == handle, DbUser.pk != user.pk)
                .first()
            )
            if taken:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail='That handle is taken',
                )
        user.handle = handle

    for flag, _, _, _, _ in _SHELVES:
        if flag in data and data[flag] is not None:
            setattr(user, flag, bool(data[flag]))

    if not user.handle and any(getattr(user, flag) for flag, *_ in _SHELVES):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail='Pick a handle before making a category public — it '
            'becomes your profile URL',
        )

    db.commit()
    db.refresh(user)
    return user


@router.get('/public/{handle}')
def public_profile(handle: str, db: Session = Depends(get_db)):
    """
    Read-only public profile: ranked lists of the categories the owner has
    opted in, best first. Fully private profiles (and unknown handles) 404
    identically, so the endpoint never confirms a private account exists.
    """
    user = db.query(DbUser).filter(DbUser.handle == handle.lower()).first()
    not_found = HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail='No public profile here'
    )
    if user is None:
        raise not_found

    shelves = []
    for flag, label, tracker_model, catalog_model, join_col in _SHELVES:
        if not getattr(user, flag):
            continue
        rows = (
            db.query(tracker_model, catalog_model)
            .join(catalog_model, getattr(tracker_model, join_col) == catalog_model.pk)
            .filter(
                tracker_model.user_id == user.pk,
                tracker_model.on_rankings.is_(True),
                tracker_model.rank.isnot(None),
            )
            .order_by(tracker_model.rank)
            .all()
        )
        shelves.append(
            {
                'category': label,
                'ranked_count': len(rows),
                'items': [
                    {
                        'rank': tracker.rank,
                        'title': item.title,
                        'year': item.year,
                        'poster_url': item.poster_url,
                    }
                    for tracker, item in rows
                ],
            }
        )

    if not shelves:
        raise not_found

    return {
        'handle': user.handle,
        'display_name': user.display_name,
        'shelves': shelves,
        'total_ranked': sum(s['ranked_count'] for s in shelves),
    }
