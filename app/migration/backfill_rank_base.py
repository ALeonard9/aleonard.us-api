"""
Re-base legacy 0-based ranks onto the API's 1-based contract.

The old site stored ranks 0-based. ``orion_import`` corrects this for TV
(``rank + 1``) but movies were imported unadjusted, so a migrated user's best
movie sits at rank 0 — it renders as "0" on the public profile and the home
Top 5, and it's off by one against every rank the API itself writes
(``reorder_rankings`` enumerates from 1; ``RankPlacement`` documents a 1-based
position).

Rather than assume which domains are affected, this shifts any shelf whose
ranks actually start at 0. Books and games were imported with a rank-0
sentinel meaning "unranked" (nulled at import), so they should already be
clean — if they aren't, this catches them too.

Idempotent: a shelf is only shifted when its minimum rank is 0, which stops
being true after the first run. Safe to re-run.

Usage::

    DATABASE_URL=postgresql://... ENV=prod \\
        python -m app.migration.backfill_rank_base [--dry-run] \\
        [--email adamleonard9@gmail.com | --all-users]
"""

import argparse
import sys

from sqlalchemy import func

from app.config import get_settings
from app.db.database import SQLALCHEMY_DATABASE_URL, SessionLocal
from app.db.models import DbUser
from app.services.shelves import SHELVES


def target_description() -> str:
    """The database this run will touch, with any password masked."""
    url = SQLALCHEMY_DATABASE_URL
    if '@' in url:
        head, tail = url.split('@', 1)
        url = f'{head.rsplit(":", 1)[0]}:***@{tail}'
    return f'ENV={get_settings().env}  DB={url}'


def _ranked_filter(tracker, user_pk):
    """The rows a re-base considers: on the rankings list with a position."""
    return (
        tracker.user_id == user_pk,
        tracker.on_rankings.is_(True),
        tracker.rank.isnot(None),
    )


def shelf_stats(db, shelf, user_pk):
    """``(lowest_rank, ranked_row_count)`` for one user's shelf."""
    return (
        db.query(
            func.min(shelf.tracker_model.rank),
            func.count(),  # pylint: disable=not-callable
        )
        .select_from(shelf.tracker_model)
        .filter(*_ranked_filter(shelf.tracker_model, user_pk))
        .one()
    )


def _shift_shelf(db, shelf, user) -> int:
    """Shift one user's ranks on one shelf up by 1. Returns rows changed."""
    tracker = shelf.tracker_model
    lowest, count = shelf_stats(db, shelf, user.pk)
    # Report every shelf, not just the ones that move — a bare "0 rows" can't
    # distinguish "already 1-based" from "wrong database" or "no data here".
    print(
        f'  {shelf.category:7} ranked={count:5} lowest_rank={lowest} '
        f'{"-> re-basing" if lowest == 0 else "-> no change"}'
    )
    if lowest != 0:
        return 0
    return (
        db.query(tracker)
        .filter(*_ranked_filter(tracker, user.pk))
        .update({tracker.rank: tracker.rank + 1}, synchronize_session=False)
    )


def run_backfill(db, email: str = None, dry_run: bool = False) -> int:
    """
    Re-base every affected shelf on an existing session. Returns rows changed.

    A dry run undoes its own writes via a SAVEPOINT rather than rolling back
    the whole transaction, so it can't discard anything the caller had
    pending.
    """
    print(target_description())
    users = db.query(DbUser)
    if email:
        users = users.filter(DbUser.email == email)
    users = users.all()
    if email and not users:
        print(f'No user with email {email} on this database', file=sys.stderr)
        return 0

    changed = 0
    savepoint = db.begin_nested()
    for user in users:
        print(f'{user.email} (pk={user.pk}):')
        for shelf in SHELVES:
            changed += _shift_shelf(db, shelf, user)

    if dry_run:
        savepoint.rollback()
        print(f'DRY RUN — {changed} rows would change')
    else:
        savepoint.commit()
        db.commit()
        print(f'Done — {changed} rows changed')
    return changed


def backfill(email: str = None, dry_run: bool = False) -> int:
    """Open a session and re-base. Returns the number of rows changed."""
    db = SessionLocal()
    try:
        return run_backfill(db, email=email, dry_run=dry_run)
    finally:
        db.close()


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dry-run', action='store_true')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--email', help='Re-base a single user')
    group.add_argument('--all-users', action='store_true', help='Re-base every user')
    args = parser.parse_args()
    backfill(email=None if args.all_users else args.email, dry_run=args.dry_run)


if __name__ == '__main__':
    main()
