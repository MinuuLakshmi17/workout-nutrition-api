# Operations

Start: `docker compose up --build -d`

Migrate: `docker compose exec api alembic upgrade head`

Logs: `docker compose logs -f api worker`

Stop: `docker compose down`

Rollback: `alembic downgrade -1`

Production: keep JWT secrets out of source control, use TLS, managed PostgreSQL/Redis, backups, monitoring, and controlled migrations.
