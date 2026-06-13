"""
This module contains the API routes for Video Games.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models_sandbox import DbVideoGame, DbUserVideoGame
from app.auth.oauth2 import get_current_user
from app.schemas.schemas_sandbox import (
    VideoGameCreate,
    VideoGameResponse,
    VideoGameUpdate,
    UserVideoGameCreate,
    UserVideoGameResponse,
    UserVideoGameUpdate,
)

router = APIRouter(prefix='/v1', tags=['Video Games'])


# Global Entity Endpoints
@router.get('/games', response_model=List[VideoGameResponse])
def get_all_games(db: Session = Depends(get_db)):
    return db.query(DbVideoGame).all()


@router.post(
    '/games', response_model=VideoGameResponse, status_code=status.HTTP_201_CREATED
)
def create_game(request: VideoGameCreate, db: Session = Depends(get_db)):
    if request.igdb:
        existing = (
            db.query(DbVideoGame).filter(DbVideoGame.igdb == request.igdb).first()
        )
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Game IGDB ID already exists',
            )

    new_game = DbVideoGame(**request.model_dump())
    db.add(new_game)
    db.commit()
    db.refresh(new_game)
    return new_game


@router.put('/games/{game_id}', response_model=VideoGameResponse)
def update_game(game_id: str, request: VideoGameUpdate, db: Session = Depends(get_db)):
    game = db.query(DbVideoGame).filter(DbVideoGame.id == game_id).first()
    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Game not found'
        )

    update_data = request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(game, key, value)

    db.commit()
    db.refresh(game)
    return game


@router.delete('/games/{game_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_game(game_id: str, db: Session = Depends(get_db)):
    game = db.query(DbVideoGame).filter(DbVideoGame.id == game_id).first()
    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Game not found'
        )
    db.delete(game)
    db.commit()
    return None


# User Tracker Endpoints
@router.get('/users/me/games', response_model=List[UserVideoGameResponse])
def get_user_games(
    db: Session = Depends(get_db), current_user: list = Depends(get_current_user)
):
    return (
        db.query(DbUserVideoGame)
        .filter(DbUserVideoGame.user_id == current_user[0].pk)
        .all()
    )


@router.post(
    '/users/me/games/{game_id}',
    response_model=UserVideoGameResponse,
    status_code=status.HTTP_201_CREATED,
)
def mark_game(
    game_id: str,
    request: UserVideoGameCreate,
    db: Session = Depends(get_db),
    current_user: list = Depends(get_current_user),
):
    game = db.query(DbVideoGame).filter(DbVideoGame.id == game_id).first()
    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Game not found'
        )

    existing_tracker = (
        db.query(DbUserVideoGame)
        .filter(
            DbUserVideoGame.user_id == current_user[0].pk,
            DbUserVideoGame.game_id == game.pk,
        )
        .first()
    )
    if existing_tracker:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail='Game already marked'
        )

    new_tracker = DbUserVideoGame(
        user_id=current_user[0].pk, game_id=game.pk, **request.model_dump()
    )
    db.add(new_tracker)
    db.commit()
    db.refresh(new_tracker)
    return new_tracker


@router.put('/users/me/games/{game_id}', response_model=UserVideoGameResponse)
def update_user_game(
    game_id: str,
    request: UserVideoGameUpdate,
    db: Session = Depends(get_db),
    current_user: list = Depends(get_current_user),
):
    game = db.query(DbVideoGame).filter(DbVideoGame.id == game_id).first()
    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Game not found'
        )

    tracker = (
        db.query(DbUserVideoGame)
        .filter(
            DbUserVideoGame.user_id == current_user[0].pk,
            DbUserVideoGame.game_id == game.pk,
        )
        .first()
    )
    if not tracker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Game not marked'
        )

    update_data = request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(tracker, key, value)

    db.commit()
    db.refresh(tracker)
    return tracker


@router.delete('/users/me/games/{game_id}', status_code=status.HTTP_204_NO_CONTENT)
def unmark_game(
    game_id: str,
    db: Session = Depends(get_db),
    current_user: list = Depends(get_current_user),
):
    game = db.query(DbVideoGame).filter(DbVideoGame.id == game_id).first()
    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Game not found'
        )

    tracker = (
        db.query(DbUserVideoGame)
        .filter(
            DbUserVideoGame.user_id == current_user[0].pk,
            DbUserVideoGame.game_id == game.pk,
        )
        .first()
    )
    if not tracker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Game not marked'
        )

    db.delete(tracker)
    db.commit()
    return None
