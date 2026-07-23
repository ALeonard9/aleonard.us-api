[![Pylint](https://github.com/ALeonard9/druthers-api/actions/workflows/lint.yaml/badge.svg?branch=main)](https://github.com/ALeonard9/druthers-api/actions/workflows/lint.yaml)
[![Pytest](https://github.com/ALeonard9/druthers-api/actions/workflows/test.yaml/badge.svg?branch=main)](https://github.com/ALeonard9/druthers-api/actions/workflows/test.yaml)
[![Snyk SCA & SAST](https://github.com/ALeonard9/druthers-api/actions/workflows/security_main.yaml/badge.svg?branch=main)](https://github.com/ALeonard9/druthers-api/actions/workflows/security_main.yaml)

# aleonard.us API

Personal API for [aleonard.us](https://www.aleonard.us) — a JWT-authenticated FastAPI service with role-based user management, auto-generated OpenAPI docs, and CI/CD with Snyk security scanning.

## Features

- **JWT Authentication** — Login endpoint returns a bearer token for subsequent requests
- **User CRUD** — Create, read, update, delete users with email validation and duplicate detection
- **Role-Based Access Control** — Admins manage all users; regular users can only access their own account
- **Auto-generated Docs** — Swagger UI at `/docs`, OpenAPI spec at `/openapi.json`
- **Containerized** — Multi-arch Docker images, Python 3.14 on Alpine
- **Security Pipeline** — Snyk SCA, SAST, and container scans on every PR and push

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | [FastAPI](https://fastapi.tiangolo.com/) |
| ORM | [SQLAlchemy](https://www.sqlalchemy.org/) |
| Validation | [Pydantic](https://docs.pydantic.dev/) |
| Auth | JWT via [PyJWT](https://github.com/jpadilla/pyjwt) + OAuth2 |
| Database | PostgreSQL (SQLite for local dev) |
| Container | Docker, Alpine 3.22, Python 3.14 |
| CI/CD | GitHub Actions, Snyk |

## Quick Start

### Local

```bash
git clone https://github.com/ALeonard9/druthers-api.git
cd druthers-api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements/dev.txt
uvicorn app.run:app --reload
```

### Docker (preferred)

```bash
docker compose -f dc-dev.yml --env-file env/dev.env up -d
```

The API is available at `http://localhost:8000`. Open `http://localhost:8000/docs` for Swagger UI.

## Environment Variables

Create a `.env` file in the project root:

```plaintext
ENV=dev
LOG_LEVEL=INFO
JWT_SECRET_KEY=<your-secret-key>

ADMIN_DISPLAY_NAME=<admin-name>
ADMIN_PASSWORD=<admin-password>
ADMIN_EMAIL=<admin-email>

POSTGRES_USER=functional_data_api_dev
POSTGRES_PASSWORD=<db-password>
POSTGRES_HOST=m3_phoenix_db_dev
POSTGRES_DB=phoenix
POSTGRES_PORT=5432
POSTGRES_EXPOSED_PORT=5430
POSTGRES_CONNECTION_PORT=5432

LOKI_URL=http://loki:3100
COMPOSE_PROJECT_NAME=phoenix_dev
```

### Notable Env Vars

| Variable | Purpose |
|---|---|
| `ENV` | `local` — drops/recreates tables on startup; `dev` — persistent DB |
| `JWT_SECRET_KEY` | HMAC signing key for JWT tokens (min 32 bytes recommended) |
| `ADMIN_*` | Credentials for the admin user created at startup |
| `POSTGRES_*` | PostgreSQL connection — defaults to a local Docker Postgres |

## API Reference

All endpoints prefixed with `/v1`. Protected endpoints require `Authorization: Bearer <token>`.

### Authentication

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/v1/auth/token` | No | Login with email + password, returns JWT |

### Users

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/v1/users` | No | Register a new user |
| `GET` | `/v1/users` | Admin | List all users |
| `GET` | `/v1/users/{uuid}` | User | Get own user (any) or any user (admin) |
| `PUT` | `/v1/users/{uuid}` | User | Update own account (any) or any (admin) |
| `DELETE` | `/v1/users/{uuid}` | User | Delete own account (any) or any (admin) |

### Sandbox Data Entities

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/v1/{entity}` | No | List global entities (countries, movies, tv-shows, games, books) |
| `POST` | `/v1/{entity}` | Admin | Create a new global entity |
| `PUT` | `/v1/{entity}/{id}` | Admin | Update a global entity |
| `DELETE` | `/v1/{entity}/{id}` | Admin | Delete a global entity |
| `GET` | `/v1/users/me/{entity}` | User | List user's tracked entities |
| `POST` | `/v1/users/me/{entity}/{id}`| User | Mark entity as tracked (visited, watched, played, etc.) |
| `PUT` | `/v1/users/me/{entity}/{id}`| User | Update tracking details for an entity |
| `DELETE` | `/v1/users/me/{entity}/{id}`| User | Remove entity from tracker |

*(Note: TV Shows also include nested `/episodes` and `/users/me/episodes` endpoints.)*

### Docs

| Path | Description |
|---|---|
| `/docs` | Swagger UI |
| `/redoc` | ReDoc |
| `/openapi.json` | OpenAPI schema |

## Testing

```bash
task test             # pytest with coverage and HTML reports
                      # or just: pytest
```

Tests run in CI on every push and pull request.

## Project Scripts

This project uses a [Taskfile](https://taskfile.dev/) for common operations:

```bash
task du               # Docker compose up (dev)
task dd               # Docker compose down
task dr               # Rebuild and restart containers
task test             # Run pytest with coverage
task sca              # Snyk SCA (dependency scan)
task sast             # Snyk SAST (static analysis)
task container        # Build + Snyk container scan
```

## Security Pipeline

GitHub Actions runs Snyk scans on every PR (labeled `scan`) and push to `main`:

- **SCA** — Dependency vulnerability scan
- **SAST** — Static code analysis
- **Container** — Image vulnerability scan (Dockerfile + base image)

Results are uploaded to GitHub Code Scanning for the main branch.

## Pre-commit Hooks

Pre-commit enforces code quality on every commit:

- Black (formatting)
- Pylint (linting)
- OpenAPI spec validation
- YAML/JSON validation
- Trailing whitespace, EOF fixer, debug statement checks

```bash
pip install pre-commit && pre-commit install
```

## Contributing

Fork the repo and submit a pull request.

## License

GNU General Public License v3.0. See [LICENSE](LICENSE).
