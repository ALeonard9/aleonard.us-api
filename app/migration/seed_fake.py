"""
Populate the LOCAL dev Postgres with a realistic volume of synthetic catalog
+ tracker data, using ``Faker``.

Unlike ``orion_import.py``, this is not sourced from anywhere real -- it
exists so local testing has enough data volume to catch pagination /
list-rendering / N+1-class bugs that are invisible against a single
seed-admin-only database. Titles are Faker-generated (plausible, not real
catalog entries) and every external id is drawn from a reserved range/prefix
that can never collide with a real imdb/tvmaze/igdb/googleid -- that id
namespace, not the title text, is what makes these rows safely identifiable
and distinct from real catalog data.

**Refuses to run against anything but the local dev Postgres** (checks
``ENV``/``POSTGRES_HOST``) -- this script performs destructive
delete-then-recreate writes scoped to its own fake rows, and must never be
able to reach QA or prod.

Usage::

    task seed:fake                              # populate/refresh (default --count 300)
    task seed:fake -- --count 1000              # more volume
    task seed:fake -- --wipe                    # clear fake rows only, no reseed
    task seed:fake -- --email you@example.com   # target a non-admin local user, e.g.
                                                 # whichever account Google Sign-In
                                                 # actually created when you signed in
"""

import argparse
import os
import random
import sys
from datetime import date, datetime, timedelta, timezone

from faker import Faker
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.database import SessionLocal
from app.db.models import DbUser
from app.db.models_sandbox import (
    DbBook,
    DbMovie,
    DbTVEpisode,
    DbTVShow,
    DbUserBook,
    DbUserMovie,
    DbUserTVEpisode,
    DbUserTVShow,
    DbUserVideoGame,
    DbVideoGame,
)
from app.log.logging_config import logger

# Reserved integer range for fake tvmaze/igdb ids -- far above any real id.
FAKE_ID_BASE = 900_000

fake = Faker()


def _assert_local_dev() -> None:
    """Refuse to run against anything but the local dev Postgres."""
    settings = get_settings()
    host = (settings.postgres_host or '').lower()
    is_safe_host = host in ('localhost', '127.0.0.1') or host.endswith('_dev')
    if settings.env != 'dev' or not is_safe_host:
        logger.error(
            'seed_fake refuses to run: ENV=%s POSTGRES_HOST=%s does not look '
            'like the local dev Postgres. This script performs destructive '
            'writes and must never touch QA or prod.',
            settings.env,
            settings.postgres_host,
        )
        sys.exit(2)


def _target_user(session: Session, email: str = None) -> DbUser:
    """
    Look up the user to attach fake tracker rows to.

    Defaults to the seed admin (``ADMIN_EMAIL``, same env var the app's own
    bootstrap uses). Pass ``--email`` to target a different local user
    instead -- e.g. whichever account Google Sign-In actually creates when
    you sign in locally, which is a different row than the seed admin.
    """
    email = email or os.getenv('ADMIN_EMAIL')
    if not email:
        logger.error(
            'ADMIN_EMAIL is not set and no --email given -- cannot attach '
            'fake tracker rows'
        )
        sys.exit(2)
    user = session.query(DbUser).filter_by(email=email).one_or_none()
    if user is None:
        logger.error(
            'No local user with email %s -- sign in once (or start the API '
            'so the seed admin is created) and then re-run.',
            email,
        )
        sys.exit(2)
    return user


def _fake_completed_at() -> date:
    return fake.date_between(start_date='-5y', end_date='today')


def _fake_ranked_at() -> datetime:
    return fake.date_time_between(start_date='-5y', end_date='now', tzinfo=timezone.utc)


def _next_rank(session: Session, model, admin: DbUser) -> int:
    """
    First free 1-based rank for this user/domain.

    Starts past any pre-existing ranked rows (e.g. from a prior
    ``task import:orion`` run in the same local DB) so seeding never produces
    duplicate rank numbers.
    """
    current_max = (
        session.query(model.rank)
        .filter(model.user_id == admin.pk, model.rank.isnot(None))
        .order_by(model.rank.desc())
        .first()
    )
    return (current_max[0] if current_max else 0) + 1


def _wipe(session: Session) -> None:
    """Delete every row this script owns, children before parents (FKs)."""
    movie_ids = [
        pk
        for (pk,) in session.query(DbMovie.pk).filter(DbMovie.imdb.like('ttfakemovie%'))
    ]
    show_ids = [
        pk
        for (pk,) in session.query(DbTVShow.pk).filter(DbTVShow.imdb.like('ttfaketv%'))
    ]
    episode_ids = (
        [
            pk
            for (pk,) in session.query(DbTVEpisode.pk).filter(
                DbTVEpisode.tv_show_id.in_(show_ids)
            )
        ]
        if show_ids
        else []
    )
    game_ids = [
        pk
        for (pk,) in session.query(DbVideoGame.pk).filter(
            DbVideoGame.igdb >= FAKE_ID_BASE
        )
    ]
    book_ids = [
        pk for (pk,) in session.query(DbBook.pk).filter(DbBook.googleid.like('FAKE-%'))
    ]

    if episode_ids:
        session.query(DbUserTVEpisode).filter(
            DbUserTVEpisode.episode_id.in_(episode_ids)
        ).delete(synchronize_session=False)
    if show_ids:
        session.query(DbUserTVShow).filter(
            DbUserTVShow.tv_show_id.in_(show_ids)
        ).delete(synchronize_session=False)
    if movie_ids:
        session.query(DbUserMovie).filter(DbUserMovie.movie_id.in_(movie_ids)).delete(
            synchronize_session=False
        )
    if game_ids:
        session.query(DbUserVideoGame).filter(
            DbUserVideoGame.game_id.in_(game_ids)
        ).delete(synchronize_session=False)
    if book_ids:
        session.query(DbUserBook).filter(DbUserBook.book_id.in_(book_ids)).delete(
            synchronize_session=False
        )

    session.query(DbTVEpisode).filter(DbTVEpisode.pk.in_(episode_ids)).delete(
        synchronize_session=False
    )
    session.query(DbTVShow).filter(DbTVShow.pk.in_(show_ids)).delete(
        synchronize_session=False
    )
    session.query(DbMovie).filter(DbMovie.pk.in_(movie_ids)).delete(
        synchronize_session=False
    )
    session.query(DbVideoGame).filter(DbVideoGame.pk.in_(game_ids)).delete(
        synchronize_session=False
    )
    session.query(DbBook).filter(DbBook.pk.in_(book_ids)).delete(
        synchronize_session=False
    )
    session.flush()


def _seed_movies(session: Session, admin: DbUser, count: int) -> None:
    ratings = ['G', 'PG', 'PG-13', 'R']
    genres = ['Drama', 'Comedy', 'Action', 'Sci-Fi', 'Horror', 'Documentary']
    movies = []
    for i in range(1, count + 1):
        year = random.randint(1970, 2026)
        movies.append(
            DbMovie(
                title=fake.catch_phrase(),
                imdb=f'ttfakemovie{i:06d}',
                release_date=datetime(
                    year, random.randint(1, 12), 1, tzinfo=timezone.utc
                ),
                rating_imdb=round(random.uniform(3.0, 9.5), 1),
                runtime=random.randint(80, 180),
                language='English',
                rated=random.choice(ratings),
                year=year,
                genre=random.choice(genres),
                director=fake.name(),
                actors=', '.join(fake.name() for _ in range(3)),
                plot=fake.paragraph(),
            )
        )
    session.add_all(movies)
    session.flush()

    ranked = [m for m in movies if random.random() < 0.7]
    rank_start = _next_rank(session, DbUserMovie, admin)
    for rank, movie in enumerate(ranked, start=rank_start):
        session.add(
            DbUserMovie(
                movie_id=movie.pk,
                user_id=admin.pk,
                on_rankings=True,
                rank=rank,
                ranked_at=_fake_ranked_at(),
                completed=1,
                completed_at=_fake_completed_at(),
            )
        )
    for movie in movies:
        if movie not in ranked:
            session.add(
                DbUserMovie(movie_id=movie.pk, user_id=admin.pk, on_watchlist=True)
            )


def _seed_tv(  # pylint: disable=too-many-locals
    session: Session, admin: DbUser, count: int
) -> None:
    genres = ['Drama', 'Comedy', 'Crime', 'Sci-Fi', 'Reality']
    ranked_trackers = []
    for i in range(1, count + 1):
        show = DbTVShow(
            title=fake.catch_phrase(),
            imdb=f'ttfaketv{i:06d}',
            tvmaze=FAKE_ID_BASE + i,
            status=random.choice(['Running', 'Ended']),
            premiered=datetime(random.randint(1990, 2025), 1, 1, tzinfo=timezone.utc),
            year=random.randint(1990, 2025),
            genre=random.choice(genres),
            network=fake.company(),
            runtime=random.choice([22, 30, 45, 60]),
            language='English',
            rating=round(random.uniform(5.0, 9.5), 1),
            summary=fake.paragraph(),
        )
        session.add(show)
        session.flush()

        is_ranked = random.random() < 0.7
        tracker = DbUserTVShow(
            tv_show_id=show.pk,
            user_id=admin.pk,
            on_rankings=is_ranked,
            on_watchlist=not is_ranked,
            rank=None,
            ranked_at=_fake_ranked_at() if is_ranked else None,
            completed_at=_fake_completed_at() if is_ranked else None,
        )
        session.add(tracker)
        if is_ranked:
            ranked_trackers.append(tracker)

        n_episodes = random.randint(6, 20)
        episodes = []
        for ep_num in range(1, n_episodes + 1):
            episodes.append(
                DbTVEpisode(
                    title=f'Episode {ep_num}',
                    tvmaze=(FAKE_ID_BASE + i) * 1000 + ep_num,
                    tv_show_id=show.pk,
                    airdate=show.premiered + timedelta(days=7 * ep_num),
                    season=1,
                    season_number=ep_num,
                )
            )
        session.add_all(episodes)
        session.flush()

        if is_ranked:
            watched_through = random.randint(0, n_episodes)
            for ep in episodes[:watched_through]:
                session.add(
                    DbUserTVEpisode(
                        episode_id=ep.pk,
                        user_id=admin.pk,
                        watched=1,
                        watched_at=_fake_ranked_at(),
                    )
                )

    rank_start = _next_rank(session, DbUserTVShow, admin)
    for rank, row in enumerate(ranked_trackers, start=rank_start):
        row.rank = rank


def _seed_games(session: Session, admin: DbUser, count: int) -> None:
    genres = ['RPG', 'Platformer', 'Shooter', 'Puzzle', 'Strategy']
    games = []
    for i in range(1, count + 1):
        games.append(
            DbVideoGame(
                title=fake.catch_phrase(),
                igdb=FAKE_ID_BASE + i,
                release_date=datetime(
                    random.randint(1990, 2026), 1, 1, tzinfo=timezone.utc
                ),
                rating=round(random.uniform(50.0, 99.0), 1),
                time_to_beat=random.randint(5, 80),
                slug=f'fake-game-{i:06d}',
                year=random.randint(1990, 2026),
                genre=random.choice(genres),
                platforms=random.choice(['PC', 'PS5', 'Switch', 'Xbox']),
                summary=fake.paragraph(),
            )
        )
    session.add_all(games)
    session.flush()

    ranked = [g for g in games if random.random() < 0.6]
    rank_start = _next_rank(session, DbUserVideoGame, admin)
    for rank, game in enumerate(ranked, start=rank_start):
        session.add(
            DbUserVideoGame(
                game_id=game.pk,
                user_id=admin.pk,
                on_rankings=True,
                rank=rank,
                ranked_at=_fake_ranked_at(),
                completed=1,
                completed_at=_fake_completed_at(),
                is_100_percent=random.random() < 0.2,
            )
        )
    for game in games:
        if game not in ranked:
            session.add(
                DbUserVideoGame(game_id=game.pk, user_id=admin.pk, on_watchlist=True)
            )


def _seed_books(session: Session, admin: DbUser, count: int) -> None:
    genres = ['Fiction', 'Non-Fiction', 'Fantasy', 'Biography', 'History']
    books = []
    for i in range(1, count + 1):
        books.append(
            DbBook(
                title=fake.sentence(nb_words=4).rstrip('.'),
                isbn=fake.isbn13(),
                googleid=f'FAKE-{i:06d}',
                authors=fake.name(),
                year=random.randint(1950, 2026),
                genre=random.choice(genres),
                description=fake.paragraph(),
                page_count=random.randint(150, 900),
                rating=round(random.uniform(2.5, 5.0), 1),
                language='English',
            )
        )
    session.add_all(books)
    session.flush()

    ranked = [b for b in books if random.random() < 0.65]
    rank_start = _next_rank(session, DbUserBook, admin)
    for rank, book in enumerate(ranked, start=rank_start):
        session.add(
            DbUserBook(
                book_id=book.pk,
                user_id=admin.pk,
                on_rankings=True,
                rank=rank,
                ranked_at=_fake_ranked_at(),
                completed=1,
                completed_at=_fake_completed_at(),
            )
        )
    for book in books:
        if book not in ranked:
            session.add(
                DbUserBook(book_id=book.pk, user_id=admin.pk, on_watchlist=True)
            )


def run_seed(count: int, wipe_only: bool, email: str = None) -> None:
    """Wipe any previously-seeded fake rows, then optionally reseed."""
    session = SessionLocal()
    try:
        admin = _target_user(session, email)
        _wipe(session)
        if wipe_only:
            session.commit()
            logger.info('seed_fake: wiped existing fake rows, no reseed requested')
            return

        # Roughly matches real prod's domain proportions (movies >> tv/books/games).
        _seed_movies(session, admin, count)
        _seed_tv(session, admin, max(10, count // 5))
        _seed_games(session, admin, max(10, count // 7))
        _seed_books(session, admin, max(10, count // 6))

        session.commit()
        logger.info(
            'seed_fake: populated %d movies + proportional tv/games/books', count
        )
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def main() -> None:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--count',
        type=int,
        default=300,
        help='Number of fake movies to generate (other domains scale off this).',
    )
    parser.add_argument(
        '--wipe',
        action='store_true',
        help='Only delete previously-seeded fake rows; do not reseed.',
    )
    parser.add_argument(
        '--email',
        default=None,
        help=(
            'Local user to attach fake tracker rows to (default: ADMIN_EMAIL). '
            'Use this to target the account Google Sign-In actually creates '
            'when you sign in locally, which is a different user than the '
            'seed admin.'
        ),
    )
    args = parser.parse_args()
    _assert_local_dev()
    run_seed(count=args.count, wipe_only=args.wipe, email=args.email)


if __name__ == '__main__':
    main()
