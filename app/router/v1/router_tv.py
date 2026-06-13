"""
This module contains the API routes for TV Shows and Episodes.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models_sandbox import DbTVShow, DbUserTVShow, DbTVEpisode, DbUserTVEpisode
from app.auth.oauth2 import get_current_user
from app.schemas.schemas_sandbox import (
    TVShowCreate,
    TVShowResponse,
    TVShowUpdate,
    UserTVShowCreate,
    UserTVShowResponse,
    UserTVShowUpdate,
    TVEpisodeCreate,
    TVEpisodeResponse,
    TVEpisodeUpdate,
    UserTVEpisodeCreate,
    UserTVEpisodeResponse,
    UserTVEpisodeUpdate,
)

router = APIRouter(prefix='/v1', tags=['TV Shows'])


# --- TV Shows Global ---
@router.get('/tv-shows', response_model=List[TVShowResponse])
def get_all_tv_shows(db: Session = Depends(get_db)):
    return db.query(DbTVShow).all()


@router.post(
    '/tv-shows', response_model=TVShowResponse, status_code=status.HTTP_201_CREATED
)
def create_tv_show(request: TVShowCreate, db: Session = Depends(get_db)):
    if request.imdb:
        existing = db.query(DbTVShow).filter(DbTVShow.imdb == request.imdb).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='TV Show IMDB ID already exists',
            )

    new_show = DbTVShow(**request.model_dump())
    db.add(new_show)
    db.commit()
    db.refresh(new_show)
    return new_show


@router.put('/tv-shows/{show_id}', response_model=TVShowResponse)
def update_tv_show(show_id: str, request: TVShowUpdate, db: Session = Depends(get_db)):
    show = db.query(DbTVShow).filter(DbTVShow.id == show_id).first()
    if not show:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='TV Show not found'
        )

    update_data = request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(show, key, value)

    db.commit()
    db.refresh(show)
    return show


@router.delete('/tv-shows/{show_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_tv_show(show_id: str, db: Session = Depends(get_db)):
    show = db.query(DbTVShow).filter(DbTVShow.id == show_id).first()
    if not show:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='TV Show not found'
        )
    db.delete(show)
    db.commit()
    return None


# --- TV Shows User Trackers ---
@router.get('/users/me/tv-shows', response_model=List[UserTVShowResponse])
def get_user_tv_shows(
    db: Session = Depends(get_db), current_user: list = Depends(get_current_user)
):
    return (
        db.query(DbUserTVShow).filter(DbUserTVShow.user_id == current_user[0].pk).all()
    )


@router.post(
    '/users/me/tv-shows/{show_id}',
    response_model=UserTVShowResponse,
    status_code=status.HTTP_201_CREATED,
)
def mark_tv_show(
    show_id: str,
    request: UserTVShowCreate,
    db: Session = Depends(get_db),
    current_user: list = Depends(get_current_user),
):
    show = db.query(DbTVShow).filter(DbTVShow.id == show_id).first()
    if not show:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='TV Show not found'
        )

    existing_tracker = (
        db.query(DbUserTVShow)
        .filter(
            DbUserTVShow.user_id == current_user[0].pk,
            DbUserTVShow.tv_show_id == show.pk,
        )
        .first()
    )
    if existing_tracker:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail='TV Show already marked'
        )

    new_tracker = DbUserTVShow(
        user_id=current_user[0].pk, tv_show_id=show.pk, **request.model_dump()
    )
    db.add(new_tracker)
    db.commit()
    db.refresh(new_tracker)
    return new_tracker


@router.put('/users/me/tv-shows/{show_id}', response_model=UserTVShowResponse)
def update_user_tv_show(
    show_id: str,
    request: UserTVShowUpdate,
    db: Session = Depends(get_db),
    current_user: list = Depends(get_current_user),
):
    show = db.query(DbTVShow).filter(DbTVShow.id == show_id).first()
    if not show:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='TV Show not found'
        )

    tracker = (
        db.query(DbUserTVShow)
        .filter(
            DbUserTVShow.user_id == current_user[0].pk,
            DbUserTVShow.tv_show_id == show.pk,
        )
        .first()
    )
    if not tracker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='TV Show not marked'
        )

    update_data = request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(tracker, key, value)

    db.commit()
    db.refresh(tracker)
    return tracker


@router.delete('/users/me/tv-shows/{show_id}', status_code=status.HTTP_204_NO_CONTENT)
def unmark_tv_show(
    show_id: str,
    db: Session = Depends(get_db),
    current_user: list = Depends(get_current_user),
):
    show = db.query(DbTVShow).filter(DbTVShow.id == show_id).first()
    if not show:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='TV Show not found'
        )

    tracker = (
        db.query(DbUserTVShow)
        .filter(
            DbUserTVShow.user_id == current_user[0].pk,
            DbUserTVShow.tv_show_id == show.pk,
        )
        .first()
    )
    if not tracker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='TV Show not marked'
        )

    db.delete(tracker)
    db.commit()
    return None


# --- TV Episodes Global ---
@router.get('/tv-shows/{show_id}/episodes', response_model=List[TVEpisodeResponse])
def get_all_episodes(show_id: str, db: Session = Depends(get_db)):
    show = db.query(DbTVShow).filter(DbTVShow.id == show_id).first()
    if not show:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='TV Show not found'
        )
    return db.query(DbTVEpisode).filter(DbTVEpisode.tv_show_id == show.pk).all()


@router.post(
    '/tv-shows/{show_id}/episodes',
    response_model=TVEpisodeResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_episode(
    show_id: str, request: TVEpisodeCreate, db: Session = Depends(get_db)
):
    show = db.query(DbTVShow).filter(DbTVShow.id == show_id).first()
    if not show:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='TV Show not found'
        )

    new_episode = DbTVEpisode(tv_show_id=show.pk, **request.model_dump())
    db.add(new_episode)
    db.commit()
    db.refresh(new_episode)
    return new_episode


@router.put('/episodes/{episode_id}', response_model=TVEpisodeResponse)
def update_episode(
    episode_id: str, request: TVEpisodeUpdate, db: Session = Depends(get_db)
):
    episode = db.query(DbTVEpisode).filter(DbTVEpisode.id == episode_id).first()
    if not episode:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Episode not found'
        )

    update_data = request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(episode, key, value)

    db.commit()
    db.refresh(episode)
    return episode


@router.delete('/episodes/{episode_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_episode(episode_id: str, db: Session = Depends(get_db)):
    episode = db.query(DbTVEpisode).filter(DbTVEpisode.id == episode_id).first()
    if not episode:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Episode not found'
        )
    db.delete(episode)
    db.commit()
    return None


# --- TV Episodes User Trackers ---
@router.post(
    '/users/me/episodes/{episode_id}',
    response_model=UserTVEpisodeResponse,
    status_code=status.HTTP_201_CREATED,
)
def mark_episode(
    episode_id: str,
    request: UserTVEpisodeCreate,
    db: Session = Depends(get_db),
    current_user: list = Depends(get_current_user),
):
    episode = db.query(DbTVEpisode).filter(DbTVEpisode.id == episode_id).first()
    if not episode:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Episode not found'
        )

    existing_tracker = (
        db.query(DbUserTVEpisode)
        .filter(
            DbUserTVEpisode.user_id == current_user[0].pk,
            DbUserTVEpisode.episode_id == episode.pk,
        )
        .first()
    )
    if existing_tracker:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail='Episode already marked'
        )

    new_tracker = DbUserTVEpisode(
        user_id=current_user[0].pk, episode_id=episode.pk, **request.model_dump()
    )
    db.add(new_tracker)
    db.commit()
    db.refresh(new_tracker)
    return new_tracker


@router.put('/users/me/episodes/{episode_id}', response_model=UserTVEpisodeResponse)
def update_user_episode(
    episode_id: str,
    request: UserTVEpisodeUpdate,
    db: Session = Depends(get_db),
    current_user: list = Depends(get_current_user),
):
    episode = db.query(DbTVEpisode).filter(DbTVEpisode.id == episode_id).first()
    if not episode:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Episode not found'
        )

    tracker = (
        db.query(DbUserTVEpisode)
        .filter(
            DbUserTVEpisode.user_id == current_user[0].pk,
            DbUserTVEpisode.episode_id == episode.pk,
        )
        .first()
    )
    if not tracker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Episode not marked'
        )

    update_data = request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(tracker, key, value)

    db.commit()
    db.refresh(tracker)
    return tracker


@router.delete(
    '/users/me/episodes/{episode_id}', status_code=status.HTTP_204_NO_CONTENT
)
def unmark_episode(
    episode_id: str,
    db: Session = Depends(get_db),
    current_user: list = Depends(get_current_user),
):
    episode = db.query(DbTVEpisode).filter(DbTVEpisode.id == episode_id).first()
    if not episode:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Episode not found'
        )

    tracker = (
        db.query(DbUserTVEpisode)
        .filter(
            DbUserTVEpisode.user_id == current_user[0].pk,
            DbUserTVEpisode.episode_id == episode.pk,
        )
        .first()
    )
    if not tracker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Episode not marked'
        )

    db.delete(tracker)
    db.commit()
    return None
