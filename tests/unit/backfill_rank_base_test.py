# pylint: disable=missing-module-docstring, missing-function-docstring
from app.db.models_sandbox import DbMovie, DbUserMovie
from app.migration.backfill_rank_base import run_backfill
from app.services.shelves import SHELVES


def _rank_movies(session, user_pk, ranks):
    """Give a user one ranked movie per entry in ``ranks``."""
    for i, rank in enumerate(ranks):
        movie = DbMovie(title=f'Film {i}', imdb=f'tt900{i}{user_pk}', year=2000)
        session.add(movie)
        session.flush()
        session.add(
            DbUserMovie(
                user_id=user_pk,
                movie_id=movie.pk,
                rank=rank,
                on_rankings=True,
                on_watchlist=False,
            )
        )
    session.commit()


def _ranks(session, user_pk):
    return sorted(
        r.rank
        for r in session.query(DbUserMovie).filter(DbUserMovie.user_id == user_pk).all()
    )


def test_shelf_registry_covers_the_four_domains():
    assert [s.category for s in SHELVES] == ['movies', 'tv', 'books', 'games']


def test_zero_based_ranks_are_rebased(test_client):
    session = test_client.test_db_session
    user = test_client.first_user
    _rank_movies(session, user.pk, [0, 1, 2, 3])

    changed = run_backfill(session, email=user.email)

    assert changed == 4
    assert _ranks(session, user.pk) == [1, 2, 3, 4]


def test_backfill_is_idempotent(test_client):
    session = test_client.test_db_session
    user = test_client.first_user
    _rank_movies(session, user.pk, [0, 1, 2])

    run_backfill(session, email=user.email)
    second = run_backfill(session, email=user.email)

    assert second == 0
    assert _ranks(session, user.pk) == [1, 2, 3]


def test_already_one_based_shelf_is_untouched(test_client):
    session = test_client.test_db_session
    user = test_client.first_user
    _rank_movies(session, user.pk, [1, 2, 3])

    assert run_backfill(session, email=user.email) == 0

    assert _ranks(session, user.pk) == [1, 2, 3]


def test_dry_run_changes_nothing(test_client):
    session = test_client.test_db_session
    user = test_client.first_user
    _rank_movies(session, user.pk, [0, 1])

    assert run_backfill(session, email=user.email, dry_run=True) == 2

    assert _ranks(session, user.pk) == [0, 1]


def test_only_the_named_user_is_rebased(test_client):
    session = test_client.test_db_session
    first, second = test_client.first_user, test_client.second_user
    _rank_movies(session, first.pk, [0, 1])
    _rank_movies(session, second.pk, [0, 1])

    run_backfill(session, email=first.email)

    assert _ranks(session, first.pk) == [1, 2]
    assert _ranks(session, second.pk) == [0, 1]


def test_reports_every_shelf_and_the_target_database(test_client, capsys):
    """A bare '0 rows' can't be diagnosed — the run must say where it looked."""
    session = test_client.test_db_session
    user = test_client.first_user
    _rank_movies(session, user.pk, [0, 1])

    run_backfill(session, email=user.email, dry_run=True)
    out = capsys.readouterr().out

    assert 'ENV=' in out and 'DB=' in out
    assert user.email in out
    # Every shelf is accounted for, moved or not.
    for category in ('movies', 'tv', 'books', 'games'):
        assert category in out
    assert 'lowest_rank=0 -> re-basing' in out
    assert 'lowest_rank=None -> no change' in out


def test_missing_user_says_so(test_client, capsys):
    assert run_backfill(test_client.test_db_session, email='nobody@example.com') == 0
    assert 'No user with email' in capsys.readouterr().err
