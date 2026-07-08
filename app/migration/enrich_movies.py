"""
Backfill OMDB detail (director/actors/genre/plot/year/rating) for movies that
were imported without it. Throttled and **resumable**: it only processes movies
still missing detail, so re-running continues where it left off (e.g. after an
OMDB daily-limit pause).

Usage::

    OMDB_API_KEY=... DATABASE_URL=... ENV=prod \\
        python -m app.migration.enrich_movies
"""

import time

from app.db.database import SessionLocal
from app.db.models_sandbox import DbMovie
from app.services.movie_search import apply_detail_to_movie, get_movie_detail

# Be polite to OMDB; a full pass over ~1300 movies takes ~20 min.
THROTTLE_SECONDS = 1.0
# get_movie_detail returns None both for genuine misses and rate limiting; a run
# of consecutive Nones almost certainly means the daily limit was hit.
STOP_AFTER_CONSECUTIVE_MISSES = 15


def run() -> None:
    """Enrich all movies still missing detail."""
    db = SessionLocal()
    try:
        pending = (
            db.query(DbMovie)
            .filter(
                DbMovie.imdb.isnot(None),
                DbMovie.plot.is_(None),
                DbMovie.director.is_(None),
            )
            .all()
        )
        total = len(pending)
        print(f'{total} movies to enrich')
        enriched = misses = consecutive = processed = 0
        for movie in pending:
            processed += 1
            detail = get_movie_detail(movie.imdb)
            if detail:
                apply_detail_to_movie(movie, detail)
                db.commit()
                enriched += 1
                consecutive = 0
            else:
                misses += 1
                consecutive += 1
            if processed % 25 == 0:
                print(f'  {processed}/{total} (enriched {enriched}, misses {misses})')
            if consecutive >= STOP_AFTER_CONSECUTIVE_MISSES:
                print(
                    f'Stopping after {consecutive} consecutive misses '
                    '(likely OMDB rate limit). Re-run later to resume.'
                )
                break
            time.sleep(THROTTLE_SECONDS)
        print(
            f'Done: enriched {enriched}, misses {misses}, '
            f'remaining ~{total - processed}'
        )
    finally:
        db.close()


if __name__ == '__main__':
    run()
