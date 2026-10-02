# API Contract

Protected endpoints require `Authorization: Bearer <access-JWT>` (short-lived,
60 minutes by default).

## Authentication

| Method & path       | Auth | Description                                              |
|---------------------|------|----------------------------------------------------------|
| `POST /auth/register` | no   | Create account. Returns the user (no tokens).             |
| `POST /auth/login`    | no   | Returns an access token + a refresh token (7-day TTL).   |
| `POST /auth/refresh`  | no   | Body: `{"refresh_token": "..."}`. Rotates the refresh token: the old one is revoked and a fresh pair is returned. Reusing a rotated token is rejected (401). |
| `POST /auth/logout`   | no   | Body: `{"refresh_token": "..."}`. Revokes the refresh token immediately. |
| `GET /auth/me`        | yes  | Current user.                                            |

Refresh tokens are JWTs carrying a unique `jti`. Each `jti` is stored in a
Redis allowlist (`refresh:{jti}` → user id, 7-day TTL). A refresh token is only
honored while its `jti` is present, so rotation and logout take effect
immediately instead of waiting out the token's natural expiry.

## Workouts

`POST /workouts` · `GET /workouts` · `GET /workouts/{id}` · `PATCH /workouts/{id}` · `DELETE /workouts/{id}` · `GET /workouts/stats`

Collection endpoints accept `page` (1+) and `page_size` (1–100) and return
`items`, `total`, `page`, and `page_size`.

`GET /workouts` filters:

- `exercise` — case-insensitive substring match on the exercise name
- `date_from`, `date_to` — `YYYY-MM-DD`, inclusive range on `performed_at`

Workout volume is `sets × reps × weight_kg`. `GET /workouts/stats` is
Redis-cached per user (120s TTL) and reports `cache_hit`; any workout
create/update/delete invalidates the key.

## Nutrition

`POST /nutrition` · `GET /nutrition` · `GET /nutrition/{id}` · `PATCH /nutrition/{id}` · `DELETE /nutrition/{id}`

Same pagination contract as workouts.

## Weekly summaries

| Method & path                 | Auth | Description                                                    |
|-------------------------------|------|----------------------------------------------------------------|
| `POST /summaries/weekly`      | yes  | Queue a summary task for the current user. Returns `task_id`.  |
| `GET /summaries/weekly/latest`| yes  | Latest stored summary, or one computed on demand.              |

Every Monday at 00:00 UTC, Celery beat fires `weekly_summary_all_users`,
which fans out one `weekly_summary` task per user. Tasks retry up to 3 times
on failure and are idempotent (upsert on `(user_id, week_start)`), so retries
and duplicate deliveries never create double rows.

## Health & operations

`GET /health` · `GET /ready` (checks Postgres + Redis, 503 when degraded)

Every response carries an `X-Request-ID` header (client-supplied or generated);
application logs are JSON lines including the request id.
