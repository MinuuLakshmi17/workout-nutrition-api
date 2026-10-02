# Verification

Performed 2026-10-02 in a clean Linux + Python 3.12 virtualenv.

- `pytest`: **15 passed**, no external services needed — SQLite in-memory DB,
  `fakeredis` for the Redis layers (stats cache, refresh-token allowlist).
- Auth: registration, login, duplicate-email rejection, bad-password rejection,
  unauthenticated access is 401.
- Refresh flow: rotation issues a new pair, reuse of a rotated token is
  rejected, logout revokes immediately, access tokens are rejected as refresh
  tokens.
- Ownership isolation: user B gets 404 on user A's workout id.
- Cache behavior: `/workouts/stats` asserts miss → hit, and a workout mutation
  asserts the cached stats are invalidated.
- Filters: exercise substring search and inclusive date-range filtering.
- Celery: beat schedule entry verified (Mondays 00:00 UTC), task retry policy
  verified (3 retries), summary upsert is idempotent on `(user_id, week_start)`.
- `black`: entire `app/`, `tests/`, `alembic/` trees formatted.
- `python -m compileall`: passed.
- Secret scan: no credentials, tokens, or private keys in the tree
  (only `dev-only`/`change-me` placeholder secrets in `.env.example`
  and docker-compose, which are meant to be replaced in production).
- Docker Compose runtime: not executed (Docker unavailable in this environment).
  `docker-compose.yml` was validated as parseable YAML.
- Production dependencies are pinned in `requirements.txt`.
