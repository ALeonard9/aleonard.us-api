# pylint: disable=missing-function-docstring, useless-return
"""
This module contains the API routes for Countries.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models_sandbox import DbCountry, DbUserCountry
from app.auth.oauth2 import get_current_user
from app.schemas.schemas_sandbox import (
    CountryCreate,
    CountryResponse,
    CountryUpdate,
    UserCountryCreate,
    UserCountryResponse,
    UserCountryUpdate,
)

router = APIRouter(prefix='/v1', tags=['Countries'])


# Global Entity Endpoints
@router.get('/countries', response_model=List[CountryResponse])
def get_all_countries(db: Session = Depends(get_db)):
    """Retrieve all countries."""
    return db.query(DbCountry).all()


@router.post(
    '/countries', response_model=CountryResponse, status_code=status.HTTP_201_CREATED
)
def create_country(request: CountryCreate, db: Session = Depends(get_db)):
    """Add a new country to the database."""
    existing = (
        db.query(DbCountry)
        .filter(DbCountry.country_code == request.country_code)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Country code already exists',
        )

    new_country = DbCountry(title=request.title, country_code=request.country_code)
    db.add(new_country)
    db.commit()
    db.refresh(new_country)
    return new_country


@router.put('/countries/{country_id}', response_model=CountryResponse)
def update_country(
    country_id: str, request: CountryUpdate, db: Session = Depends(get_db)
):
    """Update a country's details."""
    country = db.query(DbCountry).filter(DbCountry.id == country_id).first()
    if not country:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Country not found'
        )

    if request.title is not None:
        country.title = request.title
    if request.country_code is not None:
        country.country_code = request.country_code

    db.commit()
    db.refresh(country)
    return country


@router.delete('/countries/{country_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_country(country_id: str, db: Session = Depends(get_db)):
    """Delete a country from the database."""
    country = db.query(DbCountry).filter(DbCountry.id == country_id).first()
    if not country:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Country not found'
        )

    db.delete(country)
    db.commit()
    return None


# User Tracker Endpoints
@router.get('/users/me/countries', response_model=List[UserCountryResponse])
def get_user_countries(
    db: Session = Depends(get_db), current_user: list = Depends(get_current_user)
):
    """List countries the current user has visited."""
    return (
        db.query(DbUserCountry)
        .filter(DbUserCountry.user_id == current_user[0].pk)
        .all()
    )


@router.post(
    '/users/me/countries/{country_id}',
    response_model=UserCountryResponse,
    status_code=status.HTTP_201_CREATED,
)
def mark_country_visited(
    country_id: str,
    request: UserCountryCreate,
    db: Session = Depends(get_db),
    current_user: list = Depends(get_current_user),
):
    """Mark a country as visited by the current user."""
    country = db.query(DbCountry).filter(DbCountry.id == country_id).first()
    if not country:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Country not found'
        )

    existing_tracker = (
        db.query(DbUserCountry)
        .filter(
            DbUserCountry.user_id == current_user[0].pk,
            DbUserCountry.country_id == country.pk,
        )
        .first()
    )

    if existing_tracker:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Country already marked as visited',
        )

    new_tracker = DbUserCountry(
        user_id=current_user[0].pk,
        country_id=country.pk,
        rank=request.rank,
        completed=request.completed,
        notes=request.notes,
        first_visited=request.first_visited,
    )
    db.add(new_tracker)
    db.commit()
    db.refresh(new_tracker)
    return new_tracker


@router.put('/users/me/countries/{country_id}', response_model=UserCountryResponse)
def update_user_country(
    country_id: str,
    request: UserCountryUpdate,
    db: Session = Depends(get_db),
    current_user: list = Depends(get_current_user),
):
    """Update user's visit details for a country."""
    country = db.query(DbCountry).filter(DbCountry.id == country_id).first()
    if not country:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Country not found'
        )

    tracker = (
        db.query(DbUserCountry)
        .filter(
            DbUserCountry.user_id == current_user[0].pk,
            DbUserCountry.country_id == country.pk,
        )
        .first()
    )

    if not tracker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Country not marked as visited',
        )

    if request.rank is not None:
        tracker.rank = request.rank
    if request.completed is not None:
        tracker.completed = request.completed
    if request.notes is not None:
        tracker.notes = request.notes
    if request.first_visited is not None:
        tracker.first_visited = request.first_visited

    db.commit()
    db.refresh(tracker)
    return tracker


@router.delete(
    '/users/me/countries/{country_id}', status_code=status.HTTP_204_NO_CONTENT
)
def unmark_country_visited(
    country_id: str,
    db: Session = Depends(get_db),
    current_user: list = Depends(get_current_user),
):
    """Remove a country from the user's visited list."""
    country = db.query(DbCountry).filter(DbCountry.id == country_id).first()
    if not country:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Country not found'
        )

    tracker = (
        db.query(DbUserCountry)
        .filter(
            DbUserCountry.user_id == current_user[0].pk,
            DbUserCountry.country_id == country.pk,
        )
        .first()
    )

    if not tracker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Country not marked as visited',
        )

    db.delete(tracker)
    db.commit()
    return None
