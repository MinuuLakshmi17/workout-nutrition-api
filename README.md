# Workout & Nutrition API

Production-oriented multi-user backend for workout logging, nutrition tracking, cached workout statistics, and asynchronous weekly summaries.

## Stack

FastAPI · JWT (access + rotating refresh tokens) · Argon2 password hashing · PostgreSQL · SQLAlchemy 2.0 · Alembic · Redis · Celery + Beat · Docker Compose · pytest · rate limiting · pagination · structured JSON logging.

## Features

- Multi-user registration/login with short-lived signed JWT access tokens.
- Refresh-token rotation with a Redis-backed allowlist: rotation and logout revoke tokens immediately.
- Passwords are stored as strong one-way hashes, never plaintext.
- User-scoped workout and nutrition CRUD — every query is scoped to the authenticated user.
- Pagination with total/page/page_size metadata.
- Workout listing filters: exercise substring search and performed-date range.
- Redis-backed workout-stat caching with invalidation on mutations.
- Redis-backed request rate limiting (per IP, fails open if Redis is down).
- Celery weekly summaries backed by Redis: beat fires every Monday 00:00 UTC, fans out one idempotent task per user, tasks retry up to 3 times.
- PostgreSQL migrations with Alembic.
- Health and readiness endpoints (readiness checks Postgres + Redis).
- Request-ID propagation (`X-Request-ID`) and structured JSON logs.
- Dockerized API, worker, beat scheduler, PostgreSQL, and Redis.
- Automated test suite (15 tests) for authentication, refresh rotation, logout revocation, validation, ownership isolation, CRUD, pagination, filters, caching behavior, and Celery queueing — all runnable without Docker via SQLite + fakeredis.

## Run

```bash
docker compose up --build -d
docker compose exec api alembic upgrade head
```

Open `http://localhost:8000/docs` for Swagger UI.

Run tests without Docker:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pytest -q
```

## API

`POST /auth/register` · `POST /auth/login` · `POST /auth/refresh` · `POST /auth/logout` · `GET /auth/me`

`POST /workouts` · `GET /workouts` · `GET /workouts/{id}` · `PATCH /workouts/{id}` · `DELETE /workouts/{id}` · `GET /workouts/stats`

`POST /nutrition` · `GET /nutrition` · `GET /nutrition/{id}` · `PATCH /nutrition/{id}` · `DELETE /nutrition/{id}`

`POST /summaries/weekly` · `GET /summaries/weekly/latest`

`GET /health` · `GET /ready`

See [docs/API.md](docs/API.md) for the full contract, [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for design notes, and [docs/OPERATIONS.md](docs/OPERATIONS.md) for runbooks.

## Production notes

Use a strong secret from a secret manager, TLS, managed PostgreSQL/Redis, Redis authentication/TLS, controlled migrations, observability, and deployment-specific database pool sizing in production.
