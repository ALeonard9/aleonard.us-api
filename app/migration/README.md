# Legacy data migration — orion (MySQL) → phoenix (PostgreSQL)

One-off, **idempotent** ETL that imports users and the five tracker domains
(movies, TV + episodes, video games, books, countries) from the legacy `orion`
MySQL database into the modern `phoenix` PostgreSQL schema.

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

# 2. Create the target schema (against phoenix Postgres):
export DATABASE_URL=postgresql://phoenix:phoenix@127.0.0.1:5432/phoenix ENV=prod
alembic upgrade head

# 3. Dry-run (full transaction, rolled back), then the real import:
export ORION_MYSQL_URL=mysql+pymysql://root:root@127.0.0.1:13306/orion
task import:orion -- --dry-run
task import:orion
```

Requires the dev dependency `PyMySQL` (in `requirements/dev.txt`).
