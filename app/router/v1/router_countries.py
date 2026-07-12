# pylint: disable=missing-function-docstring, useless-return
"""
This module contains the API routes for Countries.

Mirrors the Movies pattern: admin-only global catalog CRUD, REST Countries
enrichment (with a catalog-wide sync/seed endpoint — the world list is
finite, so there is no external search proxy), and per-user trackers with
independent Watchlist (travel bucket list) / Rankings (visited) lists plus a
``first_visited`` date.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models_sandbox import DbCountry, DbUserCountry
from app.auth.oauth2 import get_current_user, require_admin
from app.schemas.schemas_sandbox import (
    CountryCreate,
    CountryRankingReorder,
    CountryResponse,
    CountryUpdate,
    RankPlacement,
    UserCountryCreate,
    UserCountryResponse,
    UserCountryUpdate,
)
from app.services.country_data import (
    apply_detail_to_country,
    get_country_detail,
    seed_countries,
)

router = APIRouter(prefix='/v1', tags=['Countries'])


# Global Entity Endpoints
@router.get('/countries', response_model=List[CountryResponse])
def get_all_countries(db: Session = Depends(get_db)):
    return db.query(DbCountry).order_by(DbCountry.title).all()


@router.post(
    '/countries/sync',
    response_model=List[CountryResponse],
)
def sync_countries(
    db: Session = Depends(get_db),
    current_user: list = Depends(require_admin),
):
    """Seed/refresh the full world catalog from REST Countries."""
    del current_user
    seed_countries(db)
    db.commit()
    return db.query(DbCountry).order_by(DbCountry.title).all()


@router.post(
    '/countries', response_model=CountryResponse, status_code=status.HTTP_201_CREATED
)
def create_country(
    request: CountryCreate,
    db: Session = Depends(get_db),
    current_user: list = Depends(require_admin),
):
    del current_user
    code = (request.country_code or '').lower()
    existing = db.query(DbCountry).filter(DbCountry.country_code == code).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Country code already exists',
        )

    new_country = DbCountry(**{**request.model_dump(), 'country_code': code})
    # Enrich from REST Countries on add (best effort).
    detail = get_country_detail(code)
    if detail:
        apply_detail_to_country(new_country, detail)
    db.add(new_country)
    db.commit()
    db.refresh(new_country)
    return new_country


@router.get('/countries/{country_id}', response_model=CountryResponse)
def get_country(
    country_id: str,
    db: Session = Depends(get_db),
    current_user: list = Depends(get_current_user),
):
    """Return one country's detail, enriching from REST Countries on first view."""
    del current_user
    country = _get_country(db, country_id)
    # Lazily backfill detail the first time a sparse country is opened.
    if country.region is None and country.capital is None:
        detail = get_country_detail(country.country_code)
        if detail:
            apply_detail_to_country(country, detail)
            db.commit()
            db.refresh(country)
    return country


@router.put('/countries/{country_id}', response_model=CountryResponse)
def update_country(
    country_id: str,
    request: CountryUpdate,
    db: Session = Depends(get_db),
    current_user: list = Depends(require_admin),
):
    del current_user
    country = _get_country(db, country_id)

    update_data = request.model_dump(exclude_unset=True)
    if 'country_code' in update_data and update_data['country_code']:
        update_data['country_code'] = update_data['country_code'].lower()
    for key, value in update_data.items():
        setattr(country, key, value)

    db.commit()
    db.refresh(country)
    return country


@router.delete('/countries/{country_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_country(
    country_id: str,
    db: Session = Depends(get_db),
    current_user: list = Depends(require_admin),
):
    del current_user
    country = _get_country(db, country_id)
    db.delete(country)
    db.commit()
    return None


# User Tracker Endpoints
def _get_country(db: Session, country_id: str) -> DbCountry:
    country = db.query(DbCountry).filter(DbCountry.id == country_id).first()
    if not country:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Country not found'
        )
    return country


def _get_tracker(db: Session, user_pk: int, country_pk: int):
    return (
        db.query(DbUserCountry)
        .filter(
            DbUserCountry.user_id == user_pk, DbUserCountry.country_id == country_pk
        )
        .first()
    )


def _placed_count(db: Session, user_pk: int) -> int:
    """Number of countries with an assigned rank position for this user."""
    return (
        db.query(func.count())  # pylint: disable=not-callable
        .select_from(DbUserCountry)
        .filter(
            DbUserCountry.user_id == user_pk,
            DbUserCountry.on_rankings.is_(True),
            DbUserCountry.rank.isnot(None),
        )
        .scalar()
    )


@router.get('/users/me/countries', response_model=List[UserCountryResponse])
def get_user_countries(
    db: Session = Depends(get_db), current_user: list = Depends(get_current_user)
):
    return (
        db.query(DbUserCountry)
        .filter(DbUserCountry.user_id == current_user[0].pk)
        .all()
    )


@router.put(
    '/users/me/countries/rankings/order', response_model=List[UserCountryResponse]
)
def reorder_rankings(
    request: CountryRankingReorder,
    db: Session = Depends(get_db),
    current_user: list = Depends(get_current_user),
):
    """Persist a new ranking order (drag-and-drop). Rank = position in the list."""
    user_pk = current_user[0].pk
    for position, country_id in enumerate(request.country_ids, start=1):
        country = db.query(DbCountry).filter(DbCountry.id == country_id).first()
        if not country:
            continue
        tracker = _get_tracker(db, user_pk, country.pk)
        if tracker:
            tracker.rank = position
            tracker.on_rankings = True
    db.commit()
    return (
        db.query(DbUserCountry)
        .filter(DbUserCountry.user_id == user_pk, DbUserCountry.on_rankings.is_(True))
        .order_by(DbUserCountry.rank)
        .all()
    )


@router.get('/users/me/countries/{country_id}', response_model=UserCountryResponse)
def get_user_country(
    country_id: str,
    db: Session = Depends(get_db),
    current_user: list = Depends(get_current_user),
):
    """Return the current user's tracker for one country (404 if not tracked)."""
    country = _get_country(db, country_id)
    tracker = _get_tracker(db, current_user[0].pk, country.pk)
    if not tracker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Country not marked'
        )
    return tracker


@router.put('/users/me/countries/{country_id}/rank', response_model=UserCountryResponse)
def set_country_rank(
    country_id: str,
    request: RankPlacement,
    db: Session = Depends(get_db),
    current_user: list = Depends(get_current_user),
):
    """
    Place a country at an exact 1-based position in the visited ranking,
    shifting the countries at and below that position down by one.
    """
    user_pk = current_user[0].pk
    country = _get_country(db, country_id)
    tracker = _get_tracker(db, user_pk, country.pk)
    if not tracker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Country not marked'
        )

    old_rank = tracker.rank
    tracker.on_rankings = True
    # Remove from its current slot first so the shift math excludes it.
    tracker.rank = None
    db.flush()
    if old_rank is not None:
        db.query(DbUserCountry).filter(
            DbUserCountry.user_id == user_pk,
            DbUserCountry.on_rankings.is_(True),
            DbUserCountry.rank.isnot(None),
            DbUserCountry.rank > old_rank,
        ).update(
            {DbUserCountry.rank: DbUserCountry.rank - 1}, synchronize_session=False
        )

    target = max(1, min(request.position, _placed_count(db, user_pk) + 1))
    db.query(DbUserCountry).filter(
        DbUserCountry.user_id == user_pk,
        DbUserCountry.on_rankings.is_(True),
        DbUserCountry.rank.isnot(None),
        DbUserCountry.rank >= target,
    ).update({DbUserCountry.rank: DbUserCountry.rank + 1}, synchronize_session=False)

    tracker.rank = target
    db.commit()
    db.refresh(tracker)
    return tracker


@router.post(
    '/users/me/countries/{country_id}',
    response_model=UserCountryResponse,
    status_code=status.HTTP_201_CREATED,
)
def mark_country(
    country_id: str,
    request: UserCountryCreate,
    db: Session = Depends(get_db),
    current_user: list = Depends(get_current_user),
):
    """Add a country to the user's lists (idempotent — merges list membership)."""
    user_pk = current_user[0].pk
    country = _get_country(db, country_id)
    tracker = _get_tracker(db, user_pk, country.pk)
    data = request.model_dump(exclude_unset=True)

    if tracker is None:
        was_on_rankings = False
        tracker = DbUserCountry(
            user_id=user_pk,
            country_id=country.pk,
            on_watchlist=bool(data.get('on_watchlist', False)),
            on_rankings=bool(data.get('on_rankings', False)),
            notes=data.get('notes'),
            first_visited=data.get('first_visited'),
        )
        db.add(tracker)
    else:
        was_on_rankings = tracker.on_rankings
        for key in ('on_watchlist', 'on_rankings', 'notes', 'first_visited'):
            if key in data:
                setattr(tracker, key, data[key])

    # A country only holds a rank while it's on the visited ranking AND was
    # already placed. Entering (or leaving) the ranking resets to unplaced so
    # it lands in the "to rank" bucket rather than at a stale position.
    if not tracker.on_rankings or not was_on_rankings:
        tracker.rank = None
    db.commit()
    db.refresh(tracker)
    return tracker


@router.put('/users/me/countries/{country_id}', response_model=UserCountryResponse)
def update_user_country(
    country_id: str,
    request: UserCountryUpdate,
    db: Session = Depends(get_db),
    current_user: list = Depends(get_current_user),
):
    """Update list membership, rank, notes, or first-visited for a country."""
    user_pk = current_user[0].pk
    country = _get_country(db, country_id)
    tracker = _get_tracker(db, user_pk, country.pk)
    if not tracker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Country not marked'
        )

    was_on_rankings = tracker.on_rankings
    for key, value in request.model_dump(exclude_unset=True).items():
        setattr(tracker, key, value)

    # Entering (or leaving) the ranking resets to unplaced so a stale rank
    # never places the country automatically; it lands in "to rank" instead.
    if not tracker.on_rankings or not was_on_rankings:
        tracker.rank = None

    # If it's on neither list, drop the tracker entirely.
    if not tracker.on_watchlist and not tracker.on_rankings:
        response = UserCountryResponse.model_validate(tracker)
        db.delete(tracker)
        db.commit()
        return response

    db.commit()
    db.refresh(tracker)
    return tracker


@router.delete(
    '/users/me/countries/{country_id}', status_code=status.HTTP_204_NO_CONTENT
)
def unmark_country(
    country_id: str,
    db: Session = Depends(get_db),
    current_user: list = Depends(get_current_user),
):
    user_pk = current_user[0].pk
    country = _get_country(db, country_id)
    tracker = _get_tracker(db, user_pk, country.pk)
    if not tracker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Country not marked'
        )
    db.delete(tracker)
    db.commit()
    return None
