"""
Shared rules for per-user tracker list membership.

The one-home rule (2026-07-18 product decision, aleonard.us-api#145): an item
lives on exactly one list — Watchlist, To-be-ranked, or Ranked. Moving it to
one removes it from the others. "To-be-ranked" and "Ranked" are both
``on_rankings``; the difference is whether ``rank`` is set.
"""


def enforce_single_home(tracker, requested: dict) -> None:
    """
    Resolve any watchlist/rankings overlap after a request's fields have been
    applied to ``tracker``.

    The list the request just asked for wins; when a single request asks for
    both, Rankings wins (it's the stronger claim — "I've seen this").
    Rank clearing and gap closing stay with the domain routers, which own
    their shift math.
    """
    if not (tracker.on_watchlist and tracker.on_rankings):
        return
    if requested.get('on_watchlist') and not requested.get('on_rankings'):
        tracker.on_rankings = False
    else:
        tracker.on_watchlist = False
