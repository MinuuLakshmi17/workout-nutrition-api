<div align="center">

# Workout & Nutrition API

**A production-oriented multi-user backend for workout logging, nutrition tracking, and asynchronous weekly summaries.**

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791.svg)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D.svg)](https://redis.io/)
[![Celery](https://img.shields.io/badge/Celery-5.4-37814A.svg)](https://docs.celeryq.dev/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg)](https://docs.docker.com/compose/)
[![Tests](https://img.shields.io/badge/tests-15%20passing-brightgreen.svg)](#testing)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

## Overview

A REST API that lets users log workouts and nutrition entries, view cached workout statistics, and receive automatically generated weekly summaries. Built with the stack and patterns used by real backend teams: token-based auth with rotation, per-user data isolation, caching with invalidation, background job scheduling, database migrations, and containerized deployment.

## Features

- **Secure authentication** — Short-lived JWT access tokens (60 min) with rotating refresh tokens (7 days). Refresh tokens are tracked in a Redis allowlist, so rotation and logout revoke them immediately. Passwords hashed with Argon2.
- **Strict data isolation** — Every query is scoped to the authenticated user; cross-user access by ID returns 404.
- **Workout & nutrition tracking** — Full CRUD with validation, pagination, and filters (exercise search, date range).
- **Redis caching** — Per-user workout statistics cached with a 120s TTL and invalidated on every write. Redis also backs rate limiting (fails open if Redis is down).
- **Background jobs** — Celery beat fires every Monday at 00:00 UTC and fans out one idempotent weekly-summary task per user, with automatic retries.
- **Observability** — Request-ID propagation (`X-Request-ID`), structured JSON logs, and health/readiness endpoints (readiness checks Postgres + Redis).
- **Migrations** — Versioned PostgreSQL schema via Alembic.

## Tech Stack

| Layer        | Technology                          |
|--------------|-------------------------------------|
| Framework    | FastAPI (Python 3.12)               |
| Auth         | JWT, Argon2 password hashing        |
| Database     | PostgreSQL 16, SQLAlchemy 2.0       |
| Migrations   | Alembic                             |
| Cache / Jobs | Redis 7 (cache, rate limits, Celery broker) |
| Workers      | Celery 5 + Beat                     |
| Testing      | pytest (15 tests, no Docker needed) |
| Deployment   | Docker Compose                      |

## Architecture

```
Client ──▶ FastAPI ──▶ JWT / Pydantic ──▶ SQLAlchemy ──▶ PostgreSQL
                │
                ├──▶ Redis ── stats cache · rate limits · refresh-token allowlist
                │
                └──▶ Celery ── beat (weekly schedule) ──▶ worker ──▶ PostgreSQL
```

Key design decisions are documented in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Getting Started

### Prerequisites

- Docker and Docker Compose

### Run

```bash
docker compose up --build -d
docker compose exec api alembic upgrade head
```

Open **http://localhost:8000/docs** for the interactive Swagger UI.

Useful commands:

```bash
docker compose logs -f api worker beat   # follow logs
docker compose down                      # stop everything
```

### Run the test suite (no Docker required)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
pytest -q
```

Tests run against an in-memory SQLite database and a fake Redis server — 15 tests covering authentication, refresh-token rotation and revocation, ownership isolation, validation, pagination, filters, cache behavior, and Celery task configuration.

## API Reference

All protected endpoints require `Authorization: Bearer <access-token>`.

### Auth

| Method | Path             | Description                                                      |
|--------|------------------|------------------------------------------------------------------|
| POST   | `/auth/register` | Create an account.                                               |
| POST   | `/auth/login`    | Returns an access token + refresh token pair.                    |
| POST   | `/auth/refresh`  | Rotates a refresh token; the old one is revoked.                 |
| POST   | `/auth/logout`   | Revokes a refresh token immediately.                             |
| GET    | `/auth/me`       | Returns the current user.                                        |

### Workouts

| Method | Path               | Description                                                    |
|--------|--------------------|----------------------------------------------------------------|
| POST   | `/workouts`        | Log a workout.                                                 |
| GET    | `/workouts`        | List workouts — paginated, filterable by `exercise`, `date_from`, `date_to`. |
| GET    | `/workouts/stats`  | Cached totals (reports `cache_hit`).                           |
| GET    | `/workouts/{id}`   | Get one workout.                                               |
| PATCH  | `/workouts/{id}`   | Update a workout.                                              |
| DELETE | `/workouts/{id}`   | Delete a workout.                                              |

### Nutrition

`POST /nutrition` · `GET /nutrition` (paginated) · `GET /nutrition/{id}` · `PATCH /nutrition/{id}` · `DELETE /nutrition/{id}`

### Weekly Summaries

| Method | Path                       | Description                                              |
|--------|----------------------------|----------------------------------------------------------|
| POST   | `/summaries/weekly`        | Queue a summary task for the current user.               |
| GET    | `/summaries/weekly/latest` | Fetch the latest summary (or compute one on demand).     |

### Operations

| Method | Path      | Description                                                  |
|--------|-----------|--------------------------------------------------------------|
| GET    | `/health` | Liveness probe.                                              |
| GET    | `/ready`  | Readiness probe — checks Postgres + Redis (503 if degraded). |

Full contract: [docs/API.md](docs/API.md) · Operations runbook: [docs/OPERATIONS.md](docs/OPERATIONS.md)

## Configuration

| Variable                      | Default                                            | Description                  |
|-------------------------------|----------------------------------------------------|------------------------------|
| `DATABASE_URL`                | `postgresql+psycopg://postgres:postgres@localhost:5432/workout_api` | Postgres connection |
| `REDIS_URL`                   | `redis://localhost:6379/0`                         | Redis connection             |
| `JWT_SECRET_KEY`              | `dev-only-change-me`                               | **Change in production**     |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60`                                               | Access-token lifetime        |
| `REFRESH_TOKEN_EXPIRE_DAYS`   | `7`                                                | Refresh-token lifetime       |
| `RATE_LIMIT_PER_MINUTE`       | `60`                                               | Requests per minute per IP   |
| `CORS_ORIGINS`                | `http://localhost:8000`                            | Allowed CORS origins         |

See [.env.example](.env.example) for a template.

## Project Structure

```
app/
├── main.py            # app factory, middleware (request ID, rate limiting)
├── core/              # config, JWT security, structured logging, auth deps
├── routers/           # auth, workouts, nutrition, summaries
├── models/            # SQLAlchemy models
├── schemas/           # Pydantic request/response contracts
├── services/          # stats cache, refresh-token store, summary builder
├── tasks/             # Celery app (beat schedule) + summary tasks
└── db/                # engine, session, base
alembic/               # database migrations
tests/                 # pytest suite (SQLite + fakeredis, no Docker needed)
docs/                  # API contract, architecture, operations
```

## Production Considerations

- Load `JWT_SECRET_KEY` from a secret manager; never commit real secrets.
- Terminate TLS at a reverse proxy; use managed Postgres/Redis with auth and TLS.
- Run Alembic migrations in a controlled deploy step; keep backups.
- Tune DB pool sizing and Celery concurrency for your workload; add metrics/alerting.

## License

MIT — see [LICENSE](LICENSE).
