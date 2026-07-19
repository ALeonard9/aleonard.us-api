"""
Test the recurring TV refresh job's show-selection rules.
"""

# The selection helper is the contract worth pinning here, private or not.
# pylint: disable=protected-access

from unittest.mock import patch

from app.db.models_sandbox import DbTVShow, DbUserTVShow
from app.jobs import refresh_tv


def _show(db, title, tvmaze, status):
    show = DbTVShow(title=title, tvmaze=tvmaze, status=status)
    db.add(show)
    db.flush()
    return show


def test_only_tracked_shows_are_refreshed(test_db_session):
    """
    Untracked catalog entries cost TVMaze budget for nothing.
    """
    tracked = _show(test_db_session, 'Tracked', 101, 'Running')
    _show(test_db_session, 'Untracked', 102, 'Running')
    test_db_session.add(DbUserTVShow(user_id=1, tv_show_id=tracked.pk))
    test_db_session.flush()

    picked = refresh_tv._shows_to_refresh(test_db_session, include_ended=False)
    assert [s.title for s in picked] == ['Tracked']


def test_ended_shows_are_skipped_by_default_and_included_with_all(test_db_session):
    """
    Ended shows cannot gain episodes, so they are off the nightly path but
    reachable with --all.
    """
    ended = _show(test_db_session, 'Ended Show', 201, 'Ended')
    running = _show(test_db_session, 'Running Show', 202, 'Running')
    unknown = _show(test_db_session, 'Unknown Status', 203, None)
    for s in (ended, running, unknown):
        test_db_session.add(DbUserTVShow(user_id=1, tv_show_id=s.pk))
    test_db_session.flush()

    default = {s.title for s in refresh_tv._shows_to_refresh(test_db_session, False)}
    assert default == {'Running Show', 'Unknown Status'}

    every = {s.title for s in refresh_tv._shows_to_refresh(test_db_session, True)}
    assert every == {'Ended Show', 'Running Show', 'Unknown Status'}


def test_shows_without_a_tvmaze_id_are_skipped(test_db_session):
    """
    There is nothing to refresh against without an upstream id.
    """
    show = _show(test_db_session, 'No TVMaze', None, 'Running')
    test_db_session.add(DbUserTVShow(user_id=1, tv_show_id=show.pk))
    test_db_session.flush()

    assert refresh_tv._shows_to_refresh(test_db_session, include_ended=False) == []


@patch('app.jobs.refresh_tv.sync_episodes', return_value=3)
@patch('app.jobs.refresh_tv.get_tv_show_detail', return_value=None)
@patch('app.jobs.refresh_tv.time.sleep')
def test_stops_early_after_consecutive_misses(_sleep, _detail, _sync, test_db_session):
    """
    A run of misses means rate limiting — stop rather than hammer TVMaze.
    """
    for i in range(refresh_tv.STOP_AFTER_CONSECUTIVE_MISSES + 5):
        show = _show(test_db_session, f'Show {i}', 300 + i, 'Running')
        test_db_session.add(DbUserTVShow(user_id=1, tv_show_id=show.pk))
    test_db_session.flush()

    with patch('app.jobs.refresh_tv.SessionLocal', return_value=test_db_session):
        report = refresh_tv.run()

    assert report['misses'] == refresh_tv.STOP_AFTER_CONSECUTIVE_MISSES
    # Stopped before touching every show
    assert report['shows'] < refresh_tv.STOP_AFTER_CONSECUTIVE_MISSES + 5
