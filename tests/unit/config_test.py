'''
Unit tests for app.config.Settings — focused on the invite-only allowlist
parsing added for #183 (the rest of Settings is exercised indirectly by
every other test that calls get_settings()).
'''

from app.config import Settings


def test_oauth_allowlist_emails_unset_is_none():
    """Unset (default) allowlist means the feature is a no-op."""
    settings = Settings(oauth_allowlist=None)
    assert settings.oauth_allowlist_emails is None


def test_oauth_allowlist_emails_blank_is_none():
    """A blank/whitespace-only value is treated the same as unset."""
    settings = Settings(oauth_allowlist='   ')
    assert settings.oauth_allowlist_emails is None


def test_oauth_allowlist_emails_parses_and_normalizes():
    """Entries are trimmed and lowercased so comparisons are case-insensitive."""
    settings = Settings(oauth_allowlist=' Adam@Example.com, second@example.com ,')
    assert settings.oauth_allowlist_emails == frozenset(
        {'adam@example.com', 'second@example.com'}
    )
