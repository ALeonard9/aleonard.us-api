[![lint](https://github.com/ALeonard9/druthers-api/actions/workflows/lint.yaml/badge.svg?branch=main)](https://github.com/ALeonard9/druthers-api/actions/workflows/lint.yaml)
[![tests](https://github.com/ALeonard9/druthers-api/actions/workflows/test.yaml/badge.svg?branch=main)](https://github.com/ALeonard9/druthers-api/actions/workflows/test.yaml)
[![security](https://github.com/ALeonard9/druthers-api/actions/workflows/security.yml/badge.svg?branch=main)](https://github.com/ALeonard9/druthers-api/actions/workflows/security.yml)

# Druthers API

> **[Druthers](https://druthers.io)** is social taste-sharing for the things you love —
> **Movies, TV, Books, and Games**. Track what you've watched, played, and read;
> share a formatted top-5; and find the overlap with a friend.

This repository is the **backend API** that powers it: a JWT-authenticated FastAPI
service with Google sign-in, personal API keys, per-domain trackers, and clean
auto-generated docs. It runs serverless on **Google Cloud Run** over **Neon**
Postgres in production.

## What it does

- **Sign in with Google** (OAuth) or a long-lived personal **API key** (`drk_…`) for tools/scripts
- **Track four domains** — Movies, TV (with episodes), Books, and Games — each with watched/played/read status, notes, and completion dates
- **Search & add** from external catalogs (OMDb, TMDB, Open Library, and more) behind one API
- **Role-based access** — you manage your own library; admins manage shared catalog data
- **Auto-generated docs** — Swagger UI at `/docs`, OpenAPI at `/openapi.json`
- **Secure by default** — OSS security pipeline (secrets, SAST, dependencies, container) on every PR

## Tech stack

| Layer | Technology |
|---|---|
| Framework | [FastAPI](https://fastapi.tiangolo.com/) |
| ORM / migrations | [SQLAlchemy](https://www.sqlalchemy.org/) + [Alembic](https://alembic.sqlalchemy.org/) |
| Validation | [Pydantic](https://docs.pydantic.dev/) |
| Auth | Google OAuth · JWTs · hashed `drk_` API keys |
| Database | PostgreSQL — [Neon](https://neon.tech) in prod, local Docker Postgres for dev |
| Runtime | Docker (Alpine, Python 3.14) on **Cloud Run** |
| CI/CD & security | GitHub Actions · Gitleaks · Semgrep · Trivy · Dependabot |

## Quick start

```bash
git clone https://github.com/ALeonard9/druthers-api.git
cd druthers-api
python3.14 -m venv .venv && source .venv/bin/activate
pip install -r requirements/dev.txt
uvicorn app.run:app --reload           # http://localhost:8000
```

Or with Docker: `docker compose -f dc-dev.yml --env-file env/dev.env up -d`.
Open **http://localhost:8000/docs** for the interactive API explorer.

## API reference

All endpoints are prefixed with `/v1`; protected routes require `Authorization: Bearer <token>`.

| Area | Example routes |
|---|---|
| **Auth** | `POST /v1/auth/token` · Google OAuth exchange · `POST /v1/users/me/api-keys` (mint a `drk_` key) |
| **Users** | `POST /v1/users` · `GET/PUT/DELETE /v1/users/{uuid}` |
| **Catalog** (movies · tv-shows · books · games) | `GET /v1/{domain}` · admin `POST/PUT/DELETE` |
| **My library** | `GET /v1/users/me/{domain}` · `POST/PUT/DELETE /v1/users/me/{domain}/{id}` (mark watched/played/read, notes, dates) |
| **TV episodes** | `…/tv-shows/{id}/episodes` · `…/users/me/episodes` |
| **Docs** | `/docs` (Swagger) · `/redoc` · `/openapi.json` |

## Customer-facing docs

- **Postman collection:** [`docs/druthers-api.postman_collection.json`](docs/druthers-api.postman_collection.json)
  — every route as a ready-to-run request, generated from `openapi.json` by
  [`scripts/generate_postman_collection.py`](scripts/generate_postman_collection.py).
  Import it into Postman and set the `apiToken` variable to a personal API key.
- **MCP usage guide:** [`docs/mcp-usage.md`](docs/mcp-usage.md) — connect
  Claude Desktop/Code to your Druthers library.

Both are also linked from [druthers.io/developers](https://www.druthers.io/developers).

## Development

```bash
task du            # docker compose up (dev)     task dd   # down
task test          # pytest with coverage
```

**Pre-commit** runs fast checks on every commit (Gitleaks secret scan, Black,
Pylint, OpenAPI/YAML/JSON validation). **Tests run at _pre-push_**, and only for
what changed (`pytest-testmon`) — CI runs the full suite as the merge gate.

```bash
pip install pre-commit && pre-commit install && pre-commit install --hook-type pre-push
```

## Security

Every pull request and push to `main` is scanned by an all–open-source pipeline —
**Gitleaks** (secrets), **Semgrep** (SAST), and **Trivy** (dependencies, container,
IaC) — with results in the repo's **Security** tab, plus **Dependabot** and GitHub
**push protection**. See [`SECURITY.md`](SECURITY.md) to report a vulnerability.

## Contributing

Issues and pull requests are welcome — fork, branch, and open a PR. The required
`security` check and CI must pass before merge.

## License

GNU General Public License v3.0 — see [LICENSE](LICENSE).
