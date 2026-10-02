install:
	pip install -r requirements-dev.txt
test:
	pytest -q
coverage:
	pytest --cov=app --cov-report=term-missing
run:
	uvicorn app.main:app --reload
migrate:
	alembic upgrade head
docker-up:
	docker compose up --build -d
docker-down:
	docker compose down
