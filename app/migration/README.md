# Legacy data migration — orion (MySQL) → druthers (PostgreSQL)

One-off, **idempotent** ETL that imports users and the five tracker domains
(movies, TV + episodes, video games, books, countries) from the legacy `orion`
MySQL database into the modern `druthers` PostgreSQL schema.

Betting (`bet`), crypto, and Smash Up (`smash`) are **out of scope** for this
pass (those domains are not yet modeled in the API).

## What it does

- Reads a **read-only** source (a `mysqldump` loaded into a throwaway MySQL, or
  the live DB) via `ORION_MYSQL_URL`.
- Writes to the same target the app uses (`DATABASE_URL` / `POSTGRES_*`).
- Upserts catalogs on their natural keys (`imdb`, `tvmaze`, `igdb`, `googleid`,
  `country_code`, `email`) and tracker rows on `(user, item)`, so it is safe to
  re-run — a second run reports **0 inserts, all updates**.
- Prints a reconciliation table (source vs insert/update/skip per table).

## Notes / deliberate decisions

- **Passwords are not migrated.** Legacy hashes are bcrypt (or NULL for Google
  accounts); the new stack uses Argon2 and cannot verify them. Each imported
  user gets an unusable random password — they re-auth via Google or a reset.
- Legacy `user_group` (`User`/`Admin`) is lowercased to match the new RBAC.
- `g_first` (first-completed) is preserved into `created_at` (and
  `first_visited` for countries).
- Rows with a null natural key are skipped and counted (e.g. blank-email users,
  one null `country_code`, untracked books with no `googleid`/title).

## Run it

```bash
# 1. Load a dump into a throwaway MySQL 5.7 (Apple Silicon needs --platform):
docker run -d --name orion_src --platform linux/amd64 \
  -e MYSQL_ROOT_PASSWORD=root -e MYSQL_DATABASE=orion -p 13306:3306 \
  -v "$PWD/orion_backup.sql:/docker-entrypoint-initdb.d/orion.sql:ro" mysql:5.7

# 2. Create the target schema (against druthers Postgres):
export DATABASE_URL=postgresql://druthers:druthers@127.0.0.1:5432/druthers ENV=prod
alembic upgrade head

# 3. Dry-run (full transaction, rolled back), then the real import:
export ORION_MYSQL_URL=mysql+pymysql://root:root@127.0.0.1:13306/orion
task import:orion -- --dry-run
task import:orion
```

Requires the dev dependency `PyMySQL` (in `requirements/dev.txt`).

## seed_fake.py

Populates the **local dev** Postgres with a realistic volume of synthetic
catalog + tracker data using `Faker` (already a dependency via
`requirements/test.txt`, pulled into `dev.txt`). Unlike `orion_import.py`,
this is not sourced from anywhere real — it exists purely to give local
testing enough data volume to catch pagination/list-rendering/N+1-class bugs
that are invisible against a single seed-admin-only database.

- All generated rows use collision-proof identifiers (`imdb`/`tvmaze`/`igdb`/
  `googleid` in reserved fake ranges) so they can never be mistaken for real
  catalog data at the DB level, even though titles are plausible
  Faker-generated text rather than obviously-fake gibberish.
- **Refuses to run against anything but the local dev Postgres** (checks
  `ENV`/`POSTGRES_HOST`) — this script performs destructive
  delete-then-recreate writes and must never be able to reach QA or prod.
- Re-runnable: each run deletes and recreates the fake rows it owns.
  `--wipe` clears them without reseeding. `--count N` controls volume
  (default ~300–500 catalog rows).

```bash
task seed:fake                 # populate/refresh
task seed:fake -- --count 1000 # more volume
task seed:fake -- --wipe       # clear only
```
