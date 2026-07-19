"""
Recurring maintenance jobs.

Distinct from ``app.migration``, which holds one-shot backfills that go quiet
once complete. Everything here is meant to run on a schedule, forever, and
must be idempotent.
"""
