"""
Backfill TVMaze detail (status/premiered/genres/network/rating/summary/imdb)
and episode lists for TV shows that were imported without them. Throttled and
**resumable**: it only processes shows still missing detail, so re-running
continues where it left off.

Usage::

    DATABASE_URL=... ENV=prod python -m app.migration.enrich_tv
"""

import time

from app.db.database import SessionLocal
from app.db.models_sandbox import DbTVShow
from app.services.tv_search import (
    apply_detail_to_show,
    get_tv_show_detail,
    sync_episodes,
)

# TVMaze rate limit is ~20 requests / 10 seconds; each show costs two calls
# (detail + episodes), so 1.5s keeps a full pass comfortably under it.
THROTTLE_SECONDS = 1.5
# get_tv_show_detail returns None both for genuine misses and rate limiting; a
# run of consecutive Nones almost certainly means we are being throttled hard.
STOP_AFTER_CONSECUTIVE_MISSES = 15


def run() -> None:
    """Enrich all shows still missing detail."""
    db = SessionLocal()
    try:
        pending = (
            db.query(DbTVShow)
            .filter(
                DbTVShow.tvmaze.isnot(None),
                DbTVShow.summary.is_(None),
                DbTVShow.premiered.is_(None),
            )
            .all()
        )
        total = len(pending)
        print(f'{total} shows to enrich')
        enriched = misses = consecutive = processed = episodes_created = 0
        for show in pending:
            processed += 1
            detail = get_tv_show_detail(show.tvmaze)
            if detail:
                apply_detail_to_show(show, detail)
                episodes_created += sync_episodes(db, show)
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
                    '(likely TVMaze rate limit). Re-run later to resume.'
                )
                break
            time.sleep(THROTTLE_SECONDS)
        print(
            f'Done: enriched {enriched}, new episodes {episodes_created}, '
            f'misses {misses}, remaining ~{total - processed}'
        )
    finally:
        db.close()


if __name__ == '__main__':
    run()
