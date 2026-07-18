"""
Test the Cloud Run structured-logging pieces of logging_config.
"""

import json
import logging
import sys

from app.log.logging_config import GcpJsonFormatter, running_on_cloud_run


def make_record(level, msg, exc_info=None):
    """
    Build a bare LogRecord for formatter tests.
    """
    return logging.LogRecord(
        name='aleonard_api',
        level=level,
        pathname='somefile.py',
        lineno=42,
        msg=msg,
        args=(),
        exc_info=exc_info,
    )


def test_gcp_json_formatter_shapes_entry():
    """
    Entries are single-line JSON with Cloud Logging's severity field.
    """
    out = GcpJsonFormatter().format(make_record(logging.WARNING, 'heads up'))
    entry = json.loads(out)
    assert entry['severity'] == 'WARNING'
    assert entry['message'] == 'heads up'
    assert entry['logger'] == 'aleonard_api'
    assert entry['source'] == 'somefile.py:42'
    assert '\n' not in out


def test_gcp_json_formatter_includes_traceback():
    """
    Exception tracebacks ride inside message so Error Reporting groups them.
    """
    record = None
    try:
        raise ValueError('kaboom')
    except ValueError:
        record = make_record(logging.ERROR, 'it broke', exc_info=sys.exc_info())
    entry = json.loads(GcpJsonFormatter().format(record))
    assert entry['severity'] == 'ERROR'
    assert 'it broke' in entry['message']
    assert 'Traceback' in entry['message']
    assert 'ValueError: kaboom' in entry['message']


def test_running_on_cloud_run(monkeypatch):
    """
    Detection keys off the K_SERVICE env var Cloud Run always sets.
    """
    monkeypatch.delenv('K_SERVICE', raising=False)
    assert running_on_cloud_run() is False
    monkeypatch.setenv('K_SERVICE', 'druthers-api')
    assert running_on_cloud_run() is True
