# pylint: disable=missing-function-docstring, useless-return
"""
This module contains the API routes for TV Shows and Episodes.

Mirrors the Movies pattern: admin-only global catalog CRUD, a TVMaze search
proxy, lazy enrichment on detail view, and per-user trackers with independent
Watchlist/Rankings lists plus episode-level watched marks.
"""

from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models_sandbox import DbTVShow, DbUserTVShow, DbTVEpisode, DbUserTVEpisode
from app.auth.oauth2 import get_current_user, require_admin
from app.schemas.schemas_sandbox import (
    RankPlacement,
    ScheduleEpisodeItem,
    ScheduleFrozenShow,
    ScheduleResponse,
    TVEpisodeCreate,
    TVEpisodeResponse,
    TVEpisodeUpdate,
    TVRankingReorder,
    TVShowCreate,
    TVShowResponse,
    TVShowSearchResult,
    TVShowSummary,
    TVShowUpdate,
    UserTVEpisodeResponse,
    UserTVShowCreate,
    UserTVShowResponse,
    UserTVShowUpdate,
)
from app.services.tv_search import (
    apply_detail_to_show,
    get_tv_show_detail,
    search_tv_shows as tvmaze_search_shows,
    sync_episodes,
)
from app.services.search_correction import correct_query

router = APIRouter(prefix='/v1', tags=['TV'])


# Global Entity Endpoints
@router.get('/tv-shows', response_model=List[TVShowSummary])
def get_all_tv_shows(db: Session = Depends(get_db)):
    return db.query(DbTVShow).all()


@router.get('/tv-shows/search', response_model=List[TVShowSearchResult])
def search_tv_shows_endpoint(
    q: str,
    current_user: list = Depends(get_current_user),
):
    del current_user  # any authenticated user may search
    results = tvmaze_search_shows(q)
    if not results:
        corrected = correct_query(q)
        if corrected:
            results = tvmaze_search_shows(corrected)
    return results


@router.post(
    '/tv-shows', response_model=TVShowResponse, status_code=status.HTTP_201_CREATED
)
def create_tv_show(
    request: TVShowCreate,
    db: Session = Depends(get_db),
    current_user: list = Depends(require_admin),
):
    del current_user
    if request.tvmaze:
        existing = db.query(DbTVShow).filter(DbTVShow.tvmaze == request.tvmaze).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='TV Show tvmaze id already exists',
            )
    if request.imdb:
        existing = db.query(DbTVShow).filter(DbTVShow.imdb == request.imdb).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='TV Show imdb already exists',
            )

    new_show = DbTVShow(**request.model_dump())
    # Enrich from TVMaze on add so detail/filtering work immediately, and pull
    # the episode list while we're at it (both best effort).
    detail = get_tv_show_detail(request.tvmaze)
    if detail:
        apply_detail_to_show(new_show, detail)
    db.add(new_show)
    db.flush()
    sync_episodes(db, new_show)
    db.commit()
    db.refresh(new_show)
    return new_show


@router.get('/tv-shows/{show_id}', response_model=TVShowResponse)
def get_tv_show(
    show_id: str,
    db: Session = Depends(get_db),
    current_user: list = Depends(get_current_user),
):
    """Return one show's full detail, enriching from TVMaze on first view."""
    del current_user
    show = _get_show(db, show_id)
    # Lazily backfill detail + episodes the first time a sparse show is opened.
    if show.summary is None and show.premiered is None:
        detail = get_tv_show_detail(show.tvmaze)
        if detail:
            apply_detail_to_show(show, detail)
            sync_episodes(db, show)
            db.commit()
            db.refresh(show)
    return show


@router.put('/tv-shows/{show_id}', response_model=TVShowResponse)
def update_tv_show(
    show_id: str,
    request: TVShowUpdate,
    db: Session = Depends(get_db),
    current_user: list = Depends(require_admin),
):
    del current_user
    show = _get_show(db, show_id)

    update_data = request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(show, key, value)

    db.commit()
    db.refresh(show)
    return show


@router.delete('/tv-shows/{show_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_tv_show(
    show_id: str,
    db: Session = Depends(get_db),
    current_user: list = Depends(require_admin),
):
    del current_user
    show = _get_show(db, show_id)
    db.delete(show)
    db.commit()
    return None


# Episode Catalog Endpoints
@router.get('/tv-shows/{show_id}/episodes', response_model=List[TVEpisodeResponse])
def get_all_episodes(show_id: str, db: Session = Depends(get_db)):
    show = _get_show(db, show_id)
    return (
        db.query(DbTVEpisode)
        .filter(DbTVEpisode.tv_show_id == show.pk)
        .order_by(DbTVEpisode.season, DbTVEpisode.season_number)
        .all()
    )


@router.post(
    '/tv-shows/{show_id}/episodes/sync',
    response_model=List[TVEpisodeResponse],
)
def sync_show_episodes(
    show_id: str,
    db: Session = Depends(get_db),
    current_user: list = Depends(require_admin),
):
    """Refresh the episode list from TVMaze (for ongoing shows)."""
    del current_user
    show = _get_show(db, show_id)
    sync_episodes(db, show)
    db.commit()
    return (
        db.query(DbTVEpisode)
        .filter(DbTVEpisode.tv_show_id == show.pk)
        .order_by(DbTVEpisode.season, DbTVEpisode.season_number)
        .all()
    )


@router.post(
    '/tv-shows/{show_id}/episodes',
    response_model=TVEpisodeResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_episode(
    show_id: str,
    request: TVEpisodeCreate,
    db: Session = Depends(get_db),
    current_user: list = Depends(require_admin),
):
    del current_user
    show = _get_show(db, show_id)

    new_episode = DbTVEpisode(tv_show_id=show.pk, **request.model_dump())
    db.add(new_episode)
    db.commit()
    db.refresh(new_episode)
    return new_episode


@router.put('/episodes/{episode_id}', response_model=TVEpisodeResponse)
def update_episode(
    episode_id: str,
    request: TVEpisodeUpdate,
    db: Session = Depends(get_db),
    current_user: list = Depends(require_admin),
):
    del current_user
    episode = _get_episode(db, episode_id)

    update_data = request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(episode, key, value)

    db.commit()
    db.refresh(episode)
    return episode


@router.delete('/episodes/{episode_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_episode(
    episode_id: str,
    db: Session = Depends(get_db),
    current_user: list = Depends(require_admin),
):
    del current_user
    episode = _get_episode(db, episode_id)
    db.delete(episode)
    db.commit()
    return None


# User Tracker Endpoints
def _get_show(db: Session, show_id: str) -> DbTVShow:
    show = db.query(DbTVShow).filter(DbTVShow.id == show_id).first()
    if not show:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='TV Show not found'
        )
    return show


def _get_episode(db: Session, episode_id: str) -> DbTVEpisode:
    episode = db.query(DbTVEpisode).filter(DbTVEpisode.id == episode_id).first()
    if not episode:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='Episode not found'
        )
    return episode


def _get_tracker(db: Session, user_pk: int, show_pk: int):
    return (
        db.query(DbUserTVShow)
        .filter(DbUserTVShow.user_id == user_pk, DbUserTVShow.tv_show_id == show_pk)
        .first()
    )


def _placed_count(db: Session, user_pk: int) -> int:
    """Number of shows with an assigned rank position for this user."""
    return (
        db.query(func.count())  # pylint: disable=not-callable
        .select_from(DbUserTVShow)
        .filter(
            DbUserTVShow.user_id == user_pk,
            DbUserTVShow.on_rankings.is_(True),
            DbUserTVShow.rank.isnot(None),
        )
        .scalar()
    )


@router.get('/users/me/tv-shows', response_model=List[UserTVShowResponse])
def get_user_tv_shows(
    db: Session = Depends(get_db), current_user: list = Depends(get_current_user)
):
    return (
        db.query(DbUserTVShow).filter(DbUserTVShow.user_id == current_user[0].pk).all()
    )


@router.get('/users/me/schedule', response_model=ScheduleResponse)
def get_schedule(  # pylint: disable=too-many-locals
    db: Session = Depends(get_db),
    current_user: list = Depends(get_current_user),
    window_days: int = 5,
):
    """
    What to watch: unwatched episodes airing within +/- ``window_days`` of
    today, everything overdue and unwatched (catch-up), and shows the user
    has frozen (paused tracking on, so they're excluded from both).
    """
    user_pk = current_user[0].pk
    # airdate is stored tz-naive (see tv_search._to_date), so compare naive too.
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    window_start = now - timedelta(days=window_days)
    window_end = now + timedelta(days=window_days)

    trackers = (
        db.query(DbUserTVShow)
        .filter(
            DbUserTVShow.user_id == user_pk,
            (DbUserTVShow.on_watchlist.is_(True))
            | (DbUserTVShow.on_rankings.is_(True)),
        )
        .all()
    )
    frozen_shows = [
        ScheduleFrozenShow(show_id=t.tv_show.id, show_title=t.tv_show.title)
        for t in trackers
        if t.freeze
    ]
    active_show_pks = [t.tv_show_id for t in trackers if not t.freeze]

    upcoming: List[ScheduleEpisodeItem] = []
    catch_up: List[ScheduleEpisodeItem] = []
    if active_show_pks:
        watched_episode_pks = {
            row.episode_id
            for row in db.query(DbUserTVEpisode.episode_id).filter(
                DbUserTVEpisode.user_id == user_pk, DbUserTVEpisode.watched == 1
            )
        }
        shows_by_pk = {
            s.pk: s for s in db.query(DbTVShow).filter(DbTVShow.pk.in_(active_show_pks))
        }
        episodes = (
            db.query(DbTVEpisode)
            .filter(
                DbTVEpisode.tv_show_id.in_(active_show_pks),
                DbTVEpisode.airdate.isnot(None),
            )
            .all()
        )
        for ep in episodes:
            if ep.pk in watched_episode_pks:
                continue
            show = shows_by_pk.get(ep.tv_show_id)
            if show is None:
                continue
            item = ScheduleEpisodeItem(
                show_id=show.id,
                show_title=show.title,
                episode_id=ep.id,
                episode_title=ep.title,
                season=ep.season,
                season_number=ep.season_number,
                airdate=ep.airdate,
            )
            if window_start <= ep.airdate <= window_end:
                upcoming.append(item)
            if ep.airdate <= now:
                catch_up.append(item)

        upcoming.sort(key=lambda i: (i.airdate, i.show_title, i.season_number or 0))
        catch_up.sort(key=lambda i: (i.show_title, i.season or 0, i.season_number or 0))

    return ScheduleResponse(
        upcoming=upcoming, catch_up=catch_up, frozen_shows=frozen_shows
    )


@router.put(
    '/users/me/tv-shows/rankings/order', response_model=List[UserTVShowResponse]
)
def reorder_rankings(
    request: TVRankingReorder,
    db: Session = Depends(get_db),
    current_user: list = Depends(get_current_user),
):
    """Persist a new ranking order (drag-and-drop). Rank = position in the list."""
    user_pk = current_user[0].pk
    for position, show_id in enumerate(request.show_ids, start=1):
        show = db.query(DbTVShow).filter(DbTVShow.id == show_id).first()
        if not show:
            continue
        tracker = _get_tracker(db, user_pk, show.pk)
        if tracker:
            tracker.rank = position
            tracker.on_rankings = True
    db.commit()
    return (
        db.query(DbUserTVShow)
        .filter(DbUserTVShow.user_id == user_pk, DbUserTVShow.on_rankings.is_(True))
        .order_by(DbUserTVShow.rank)
        .all()
    )


@router.get('/users/me/tv-shows/{show_id}', response_model=UserTVShowResponse)
def get_user_tv_show(
    show_id: str,
    db: Session = Depends(get_db),
    current_user: list = Depends(get_current_user),
):
    """Return the current user's tracker for one show (404 if not tracked)."""
    show = _get_show(db, show_id)
    tracker = _get_tracker(db, current_user[0].pk, show.pk)
    if not tracker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='TV Show not marked'
        )
    return tracker


@router.put('/users/me/tv-shows/{show_id}/rank', response_model=UserTVShowResponse)
def set_show_rank(
    show_id: str,
    request: RankPlacement,
    db: Session = Depends(get_db),
    current_user: list = Depends(get_current_user),
):
    """
    Place a show at an exact 1-based position in the ranked list, shifting the
    shows at and below that position down by one. Works for a not-yet-ranked
    show (jump it in) or an already-ranked one (move it).
    """
    user_pk = current_user[0].pk
    show = _get_show(db, show_id)
    tracker = _get_tracker(db, user_pk, show.pk)
    if not tracker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='TV Show not marked'
        )

    old_rank = tracker.rank
    tracker.on_rankings = True
    # Remove from its current slot first so the shift math excludes it.
    tracker.rank = None
    db.flush()
    if old_rank is not None:
        db.query(DbUserTVShow).filter(
            DbUserTVShow.user_id == user_pk,
            DbUserTVShow.on_rankings.is_(True),
            DbUserTVShow.rank.isnot(None),
            DbUserTVShow.rank > old_rank,
        ).update({DbUserTVShow.rank: DbUserTVShow.rank - 1}, synchronize_session=False)

    target = max(1, min(request.position, _placed_count(db, user_pk) + 1))
    db.query(DbUserTVShow).filter(
        DbUserTVShow.user_id == user_pk,
        DbUserTVShow.on_rankings.is_(True),
        DbUserTVShow.rank.isnot(None),
        DbUserTVShow.rank >= target,
    ).update({DbUserTVShow.rank: DbUserTVShow.rank + 1}, synchronize_session=False)

    tracker.rank = target
    db.commit()
    db.refresh(tracker)
    return tracker


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
    """Add a show to the user's lists (idempotent — merges list membership)."""
    user_pk = current_user[0].pk
    show = _get_show(db, show_id)
    tracker = _get_tracker(db, user_pk, show.pk)
    data = request.model_dump(exclude_unset=True)

    if tracker is None:
        was_on_rankings = False
        tracker = DbUserTVShow(
            user_id=user_pk,
            tv_show_id=show.pk,
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

    # A show only holds a rank while it's on the ranked list AND was already
    # placed. Entering Rankings (or leaving it) resets to unplaced so it lands
    # in the "to rank" bucket rather than at a stale/leftover position.
    if not tracker.on_rankings or not was_on_rankings:
        tracker.rank = None
    db.commit()
    db.refresh(tracker)
    return tracker


@router.put('/users/me/tv-shows/{show_id}', response_model=UserTVShowResponse)
def update_user_tv_show(
    show_id: str,
    request: UserTVShowUpdate,
    db: Session = Depends(get_db),
    current_user: list = Depends(get_current_user),
):
    """Update list membership, rank, or notes for a tracked show."""
    user_pk = current_user[0].pk
    show = _get_show(db, show_id)
    tracker = _get_tracker(db, user_pk, show.pk)
    if not tracker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='TV Show not marked'
        )

    was_on_rankings = tracker.on_rankings
    for key, value in request.model_dump(exclude_unset=True).items():
        setattr(tracker, key, value)

    # Entering Rankings (or leaving it) resets to unplaced so a stale/leftover
    # rank never places the show automatically; it lands in "to rank" instead.
    if not tracker.on_rankings or not was_on_rankings:
        tracker.rank = None

    # If it's on neither list, drop the tracker entirely.
    if not tracker.on_watchlist and not tracker.on_rankings:
        response = UserTVShowResponse.model_validate(tracker)
        db.delete(tracker)
        db.commit()
        return response

    db.commit()
    db.refresh(tracker)
    return tracker


@router.delete('/users/me/tv-shows/{show_id}', status_code=status.HTTP_204_NO_CONTENT)
def unmark_tv_show(
    show_id: str,
    db: Session = Depends(get_db),
    current_user: list = Depends(get_current_user),
):
    user_pk = current_user[0].pk
    show = _get_show(db, show_id)
    tracker = _get_tracker(db, user_pk, show.pk)
    if not tracker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail='TV Show not marked'
        )
    db.delete(tracker)
    db.commit()
    return None


# User Episode Tracker Endpoints
@router.get(
    '/users/me/tv-shows/{show_id}/episodes',
    response_model=List[UserTVEpisodeResponse],
)
def get_user_episodes(
    show_id: str,
    db: Session = Depends(get_db),
    current_user: list = Depends(get_current_user),
):
    """The current user's episode watch marks for one show."""
    show = _get_show(db, show_id)
    return (
        db.query(DbUserTVEpisode)
        .join(DbTVEpisode, DbUserTVEpisode.episode_id == DbTVEpisode.pk)
        .filter(
            DbUserTVEpisode.user_id == current_user[0].pk,
            DbTVEpisode.tv_show_id == show.pk,
        )
        .all()
    )


@router.post(
    '/users/me/episodes/{episode_id}',
    response_model=UserTVEpisodeResponse,
    status_code=status.HTTP_201_CREATED,
)
def mark_episode_watched(
    episode_id: str,
    db: Session = Depends(get_db),
    current_user: list = Depends(get_current_user),
):
    """Mark an episode watched (idempotent)."""
    user_pk = current_user[0].pk
    episode = _get_episode(db, episode_id)

    tracker = (
        db.query(DbUserTVEpisode)
        .filter(
            DbUserTVEpisode.user_id == user_pk,
            DbUserTVEpisode.episode_id == episode.pk,
        )
        .first()
    )
    if tracker is None:
        tracker = DbUserTVEpisode(user_id=user_pk, episode_id=episode.pk, watched=1)
        db.add(tracker)
    else:
        tracker.watched = 1
    db.commit()
    db.refresh(tracker)
    return tracker


@router.post(
    '/users/me/tv-shows/{show_id}/episodes/watch-all',
    response_model=List[UserTVEpisodeResponse],
)
def mark_all_episodes_watched(
    show_id: str,
    season: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: list = Depends(get_current_user),
):
    """
    Mark every episode of a show watched (idempotent), or with ``season``
    just that one season's episodes.
    """
    user_pk = current_user[0].pk
    show = _get_show(db, show_id)

    episode_query = db.query(DbTVEpisode).filter(DbTVEpisode.tv_show_id == show.pk)
    if season is not None:
        episode_query = episode_query.filter(DbTVEpisode.season == season)
    episodes = episode_query.all()
    if not episodes:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='No episodes match that show/season',
        )

    episode_pks = [e.pk for e in episodes]
    existing_by_episode = {
        tracker.episode_id: tracker
        for tracker in db.query(DbUserTVEpisode).filter(
            DbUserTVEpisode.user_id == user_pk,
            DbUserTVEpisode.episode_id.in_(episode_pks),
        )
    }
    for ep in episodes:
        tracker = existing_by_episode.get(ep.pk)
        if tracker is None:
            db.add(DbUserTVEpisode(user_id=user_pk, episode_id=ep.pk, watched=1))
        else:
            tracker.watched = 1
    db.commit()

    return (
        db.query(DbUserTVEpisode)
        .join(DbTVEpisode, DbUserTVEpisode.episode_id == DbTVEpisode.pk)
        .filter(
            DbUserTVEpisode.user_id == user_pk,
            DbUserTVEpisode.episode_id.in_(episode_pks),
        )
        .all()
    )


@router.delete(
    '/users/me/episodes/{episode_id}', status_code=status.HTTP_204_NO_CONTENT
)
def unmark_episode_watched(
    episode_id: str,
    db: Session = Depends(get_db),
    current_user: list = Depends(get_current_user),
):
    user_pk = current_user[0].pk
    episode = _get_episode(db, episode_id)
    tracker = (
        db.query(DbUserTVEpisode)
        .filter(
            DbUserTVEpisode.user_id == user_pk,
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
