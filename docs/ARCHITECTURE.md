# Architecture

Client → FastAPI → JWT/Pydantic → SQLAlchemy/PostgreSQL.

## Authentication

Short-lived access JWTs (60 min) plus rotating refresh JWTs (7 days). Each
refresh token carries a unique `jti` stored in a Redis allowlist
(`refresh:{jti}` → user id, 7-day TTL). `/auth/refresh` revokes the old `jti`
and issues a new pair; `/auth/logout` revokes immediately. An access token can
never be used as a refresh token (the `type` claim is enforced).

## Redis

Redis serves three roles:

1. **Workout statistics cache** — per-user stats, 120s TTL, invalidated on any
   workout write.
2. **Rate-limit counters** — per-IP fixed window (60 req/min); fails open if
   Redis is unreachable so the API never goes down with the cache.
3. **Refresh-token allowlist** — see above.
4. **Celery broker + result backend.**

## Background jobs

Celery beat fires `weekly_summary_all_users` every Monday 00:00 UTC. It fans
out one `weekly_summary` task per user via a Celery group. Tasks retry up to
3 times with backoff on failure and are idempotent — `build_weekly_summary`
upserts on `(user_id, week_start)`, so retries and duplicate deliveries never
create double rows.

## Data isolation

Every protected query includes the authenticated user ID, preventing
cross-user resource access by ID alone. There is no admin or cross-user read
path anywhere in the API.

## Observability

Each request gets a correlation id (`X-Request-ID`, client-supplied or
generated). Application logs are JSON lines carrying the request id, method,
path, and status. `/ready` reports Postgres and Redis health (503 when
degraded); `/health` is a cheap liveness probe.
