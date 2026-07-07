# pylint: disable=missing-module-docstring, missing-function-docstring
from app.migration.orion_import import Report, _clean, _decode_blob


def test_clean_trims_and_nulls_empty():
    assert _clean('  hello  ') == 'hello'
    assert _clean('') is None
    assert _clean('   ') is None
    assert _clean(None) is None


def test_clean_truncates_to_limit():
    assert _clean('abcdefgh', 4) == 'abcd'
    assert _clean('ab', 4) == 'ab'


def test_decode_blob_handles_bytes_and_none():
    assert _decode_blob(None) is None
    assert _decode_blob(b'notes') == 'notes'
    assert _decode_blob('plain') == 'plain'
    # invalid utf-8 is replaced, not raised
    assert _decode_blob(b'\xff') is not None


def test_report_counts_and_render():
    report = Report()
    report.bump(report.source_counts, 'movies')
    report.bump(report.inserted, 'movies')
    report.bump(report.updated, 'movies')
    rendered = report.render()
    assert 'movies' in rendered
    assert 'source' in rendered
    assert report.inserted['movies'] == 1
