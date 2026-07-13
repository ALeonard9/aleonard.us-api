"""
Seed and enrich the country catalog from the mledoze/countries dataset:
upserts the full world list (so the travel bucket list can offer every
country) and fills region/subregion/capital/flags on existing rows.
(Population is not in the dataset; the column stays NULL until a source is
wired up.) One upstream call for the whole run — no throttling needed.

Usage::

    DATABASE_URL=... ENV=prod python -m app.migration.enrich_countries
"""

from app.db.database import SessionLocal
from app.db.models_sandbox import DbCountry
from app.services.country_data import seed_countries


def run() -> None:
    """Seed the world list and enrich existing catalog rows."""
    db = SessionLocal()
    try:
        before = db.query(DbCountry).count()
        created = seed_countries(db)
        db.commit()
        total = db.query(DbCountry).count()
        enriched = db.query(DbCountry).filter(DbCountry.region.isnot(None)).count()
        print(
            f'Done: {before} countries before, {created} created, '
            f'{total} total, {enriched} enriched'
        )
    finally:
        db.close()


if __name__ == '__main__':
    run()
