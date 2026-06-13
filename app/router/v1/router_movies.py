"""
This module contains the API routes for Movies.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models_sandbox import DbMovie, DbUserMovie
from app.auth.oauth2 import get_current_user
from app.schemas.schemas_sandbox import (
    MovieCreate,
    MovieResponse,
    MovieUpdate,
    UserMovieCreate,
    UserMovieResponse,
    UserMovieUpdate,
)

router = APIRouter(prefix='/v1', tags=['Movies'])


# Global Entity Endpoints
@router.get('/movies', response_model=List[MovieResponse])
def get_all_movies(db: Session = Depends(get_db)):
    return db.query(DbMovie).all()


@router.post(
    '/movies', response_model=MovieResponse, status_code=status.HTTP_201_CREATED
)
def create_movie(request: MovieCreate, db: Session = Depends(get_db)):
    existing = db.query(DbMovie).filter(DbMovie.imdb == request.imdb).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail='Movie imdb already exists'
        )

    new_movie = DbMovie(**request.model_dump())
    db.add(new_movie)
    db.commit()
    db.refresh(new_movie)
    return new_movie


@router.put('/movies/{movie_id}', response_model=MovieResponse)
def update_movie(movie_id: str, request: MovieUpdate, db: Session = Depends(get_db)):
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
def delete_movie(movie_id: str, db: Session = Depends(get_db)):
    movie = db.query(DbMovie).filter(DbMovie.id == movie_id).first()
    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Movie not found'
        )
    db.delete(movie)
    db.commit()
    return None


# User Tracker Endpoints
@router.get('/users/me/movies', response_model=List[UserMovieResponse])
def get_user_movies(
    db: Session = Depends(get_db), current_user: list = Depends(get_current_user)
):
    return db.query(DbUserMovie).filter(DbUserMovie.user_id == current_user[0].pk).all()


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
    movie = db.query(DbMovie).filter(DbMovie.id == movie_id).first()
    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Movie not found'
        )

    existing_tracker = (
        db.query(DbUserMovie)
        .filter(
            DbUserMovie.user_id == current_user[0].pk, DbUserMovie.movie_id == movie.pk
        )
        .first()
    )
    if existing_tracker:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail='Movie already marked'
        )

    new_tracker = DbUserMovie(
        user_id=current_user[0].pk, movie_id=movie.pk, **request.model_dump()
    )
    db.add(new_tracker)
    db.commit()
    db.refresh(new_tracker)
    return new_tracker


@router.put('/users/me/movies/{movie_id}', response_model=UserMovieResponse)
def update_user_movie(
    movie_id: str,
    request: UserMovieUpdate,
    db: Session = Depends(get_db),
    current_user: list = Depends(get_current_user),
):
    movie = db.query(DbMovie).filter(DbMovie.id == movie_id).first()
    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Movie not found'
        )

    tracker = (
        db.query(DbUserMovie)
        .filter(
            DbUserMovie.user_id == current_user[0].pk, DbUserMovie.movie_id == movie.pk
        )
        .first()
    )
    if not tracker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Movie not marked'
        )

    update_data = request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(tracker, key, value)

    db.commit()
    db.refresh(tracker)
    return tracker


@router.delete('/users/me/movies/{movie_id}', status_code=status.HTTP_204_NO_CONTENT)
def unmark_movie(
    movie_id: str,
    db: Session = Depends(get_db),
    current_user: list = Depends(get_current_user),
):
    movie = db.query(DbMovie).filter(DbMovie.id == movie_id).first()
    if not movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Movie not found'
        )

    tracker = (
        db.query(DbUserMovie)
        .filter(
            DbUserMovie.user_id == current_user[0].pk, DbUserMovie.movie_id == movie.pk
        )
        .first()
    )
    if not tracker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Movie not marked'
        )

    db.delete(tracker)
    db.commit()
    return None
