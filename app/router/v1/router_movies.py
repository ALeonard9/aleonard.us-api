# pylint: disable=missing-function-docstring, useless-return
"""
This module contains the API routes for Movies.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models_sandbox import DbMovie, DbUserMovie
from app.auth.oauth2 import get_current_user, require_admin
from app.schemas.schemas_sandbox import (
    MovieCreate,
    MovieResponse,
    MovieSearchResult,
    MovieUpdate,
    RankPlacement,
    RankingReorder,
    UserMovieCreate,
    UserMovieResponse,
    UserMovieUpdate,
)
from app.services.movie_search import (
    apply_detail_to_movie,
    get_movie_detail,
    search_movies as omdb_search_movies,
)

router = APIRouter(prefix='/v1', tags=['Movies'])


# Global Entity Endpoints
@router.get('/movies', response_model=List[MovieResponse])
def get_all_movies(db: Session = Depends(get_db)):
    return db.query(DbMovie).all()


@router.get('/movies/search', response_model=List[MovieSearchResult])
def search_movies_endpoint(
    q: str,
    current_user: list = Depends(get_current_user),
):
    del current_user  # any authenticated user may search
    return omdb_search_movies(q)


@router.post(
    '/movies', response_model=MovieResponse, status_code=status.HTTP_201_CREATED
)
def create_movie(
    request: MovieCreate,
    db: Session = Depends(get_db),
    current_user: list = Depends(get_current_user),
):
    # Any signed-in user may add to the shared catalog (the add-from-search
    # flow); editing and deleting catalog entries stay admin-only.
    del current_user
    existing = db.query(DbMovie).filter(DbMovie.imdb == request.imdb).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail='Movie imdb already exists'
        )

    new_movie = DbMovie(**request.model_dump())
    # Enrich from OMDB on add so detail/filtering work immediately (best effort).
    detail = get_movie_detail(request.imdb)
    if detail:
        apply_detail_to_movie(new_movie, detail)
    db.add(new_movie)
    db.commit()
    db.refresh(new_movie)
    return new_movie


@router.get('/movies/{movie_id}', response_model=MovieResponse)
def get_movie(
    movie_id: str,
    db: Session = Depends(get_db),
    current_user: list = Depends(get_current_user),
):
    """Return one movie's full detail, enriching from OMDB on first view."""
    del current_user
    movie = _get_movie(db, movie_id)
    # Lazily backfill detail the first time a sparse movie is opened.
    if movie.plot is None and movie.director is None:
        detail = get_movie_detail(movie.imdb)
        if detail:
            apply_detail_to_movie(movie, detail)
            db.commit()
            db.refresh(movie)
    return movie


@router.put('/movies/{movie_id}', response_model=MovieResponse)
def update_movie(
    movie_id: str,
    request: MovieUpdate,
    db: Session = Depends(get_db),
    current_user: list = Depends(require_admin),
):
    del current_user
    movie = db.query(DbMovie).filter(DbMovie.id == movie_id).first()
    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Movie not found'
        )

    update_data = request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(movie, key, value)

    db.commit()
    db.refresh(movie)
    return movie


@router.delete('/movies/{movie_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_movie(
    movie_id: str,
    db: Session = Depends(get_db),
    current_user: list = Depends(require_admin),
):
    del current_user
    movie = db.query(DbMovie).filter(DbMovie.id == movie_id).first()
    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Movie not found'
        )
    db.delete(movie)
    db.commit()
    return None


# User Tracker Endpoints
def _get_movie(db: Session, movie_id: str) -> DbMovie:
    movie = db.query(DbMovie).filter(DbMovie.id == movie_id).first()
    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Movie not found'
        )
    return movie


def _get_tracker(db: Session, user_pk: int, movie_pk: int):
    return (
        db.query(DbUserMovie)
        .filter(DbUserMovie.user_id == user_pk, DbUserMovie.movie_id == movie_pk)
        .first()
    )


def _placed_count(db: Session, user_pk: int) -> int:
    """Number of movies with an assigned rank position for this user."""
    return (
        db.query(func.count())  # pylint: disable=not-callable
        .select_from(DbUserMovie)
        .filter(
            DbUserMovie.user_id == user_pk,
            DbUserMovie.on_rankings.is_(True),
            DbUserMovie.rank.isnot(None),
        )
        .scalar()
    )


@router.get('/users/me/movies', response_model=List[UserMovieResponse])
def get_user_movies(
    db: Session = Depends(get_db), current_user: list = Depends(get_current_user)
):
    return db.query(DbUserMovie).filter(DbUserMovie.user_id == current_user[0].pk).all()


@router.get('/users/me/movies/{movie_id}', response_model=UserMovieResponse)
def get_user_movie(
    movie_id: str,
    db: Session = Depends(get_db),
    current_user: list = Depends(get_current_user),
):
    """Return the current user's tracker for one movie (404 if not tracked)."""
    movie = _get_movie(db, movie_id)
    tracker = _get_tracker(db, current_user[0].pk, movie.pk)
    if not tracker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Movie not marked'
        )
    return tracker


@router.put('/users/me/movies/rankings/order', response_model=List[UserMovieResponse])
def reorder_rankings(
    request: RankingReorder,
    db: Session = Depends(get_db),
    current_user: list = Depends(get_current_user),
):
    """Persist a new ranking order (drag-and-drop). Rank = position in the list."""
    user_pk = current_user[0].pk
    for position, movie_id in enumerate(request.movie_ids, start=1):
        movie = db.query(DbMovie).filter(DbMovie.id == movie_id).first()
        if not movie:
            continue
        tracker = _get_tracker(db, user_pk, movie.pk)
        if tracker:
            tracker.rank = position
            tracker.on_rankings = True
    db.commit()
    return (
        db.query(DbUserMovie)
        .filter(DbUserMovie.user_id == user_pk, DbUserMovie.on_rankings.is_(True))
        .order_by(DbUserMovie.rank)
        .all()
    )


@router.put('/users/me/movies/{movie_id}/rank', response_model=UserMovieResponse)
def set_movie_rank(
    movie_id: str,
    request: RankPlacement,
    db: Session = Depends(get_db),
    current_user: list = Depends(get_current_user),
):
    """
    Place a movie at an exact 1-based position in the ranked list, shifting the
    movies at and below that position down by one. Works for a not-yet-ranked
    movie (jump it in) or an already-ranked one (move it).
    """
    user_pk = current_user[0].pk
    movie = _get_movie(db, movie_id)
    tracker = _get_tracker(db, user_pk, movie.pk)
    if not tracker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Movie not marked'
        )

    old_rank = tracker.rank
    tracker.on_rankings = True
    # Remove from its current slot first so the shift math excludes it.
    tracker.rank = None
    db.flush()
    if old_rank is not None:
        db.query(DbUserMovie).filter(
            DbUserMovie.user_id == user_pk,
            DbUserMovie.on_rankings.is_(True),
            DbUserMovie.rank.isnot(None),
            DbUserMovie.rank > old_rank,
        ).update({DbUserMovie.rank: DbUserMovie.rank - 1}, synchronize_session=False)

    target = max(1, min(request.position, _placed_count(db, user_pk) + 1))
    db.query(DbUserMovie).filter(
        DbUserMovie.user_id == user_pk,
        DbUserMovie.on_rankings.is_(True),
        DbUserMovie.rank.isnot(None),
        DbUserMovie.rank >= target,
    ).update({DbUserMovie.rank: DbUserMovie.rank + 1}, synchronize_session=False)

    tracker.rank = target
    db.commit()
    db.refresh(tracker)
    return tracker


@router.post(
    '/users/me/movies/{movie_id}',
    response_model=UserMovieResponse,
    status_code=status.HTTP_201_CREATED,
)
def mark_movie(
    movie_id: str,
    request: UserMovieCreate,
    db: Session = Depends(get_db),
    current_user: list = Depends(get_current_user),
):
    """Add a movie to the user's lists (idempotent — merges list membership)."""
    user_pk = current_user[0].pk
    movie = _get_movie(db, movie_id)
    tracker = _get_tracker(db, user_pk, movie.pk)
    data = request.model_dump(exclude_unset=True)

    if tracker is None:
        was_on_rankings = False
        tracker = DbUserMovie(
            user_id=user_pk,
            movie_id=movie.pk,
            on_watchlist=bool(data.get('on_watchlist', False)),
            on_rankings=bool(data.get('on_rankings', False)),
            notes=data.get('notes'),
        )
        db.add(tracker)
    else:
        was_on_rankings = tracker.on_rankings
        for key in ('on_watchlist', 'on_rankings', 'notes'):
            if key in data:
                setattr(tracker, key, data[key])

    # A movie only holds a rank while it's on the ranked list AND was already
    # placed. Entering Rankings (or leaving it) resets to unplaced so it lands
    # in the "to rank" bucket rather than at a stale/leftover position.
    if not tracker.on_rankings or not was_on_rankings:
        tracker.rank = None
    db.commit()
    db.refresh(tracker)
    return tracker


@router.put('/users/me/movies/{movie_id}', response_model=UserMovieResponse)
def update_user_movie(
    movie_id: str,
    request: UserMovieUpdate,
    db: Session = Depends(get_db),
    current_user: list = Depends(get_current_user),
):
    """Update list membership, rank, or notes for a tracked movie."""
    user_pk = current_user[0].pk
    movie = _get_movie(db, movie_id)
    tracker = _get_tracker(db, user_pk, movie.pk)
    if not tracker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Movie not marked'
        )

    was_on_rankings = tracker.on_rankings
    for key, value in request.model_dump(exclude_unset=True).items():
        setattr(tracker, key, value)

    # Entering Rankings (or leaving it) resets to unplaced so a stale/leftover
    # rank never places the movie automatically; it lands in "to rank" instead.
    if not tracker.on_rankings or not was_on_rankings:
        tracker.rank = None

    # If it's on neither list, drop the tracker entirely.
    if not tracker.on_watchlist and not tracker.on_rankings:
        response = UserMovieResponse.model_validate(tracker)
        db.delete(tracker)
        db.commit()
        return response

    db.commit()
    db.refresh(tracker)
    return tracker


@router.delete('/users/me/movies/{movie_id}', status_code=status.HTTP_204_NO_CONTENT)
def unmark_movie(
    movie_id: str,
    db: Session = Depends(get_db),
    current_user: list = Depends(get_current_user),
):
    user_pk = current_user[0].pk
    movie = _get_movie(db, movie_id)
    tracker = _get_tracker(db, user_pk, movie.pk)
    if not tracker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Movie not marked'
        )
    db.delete(tracker)
    db.commit()
    return None
