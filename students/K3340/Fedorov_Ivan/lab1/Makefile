.PHONY: install dev migrate test run up down logs

install:
	python -m pip install -r requirements-dev.txt

migrate:
	alembic upgrade head

run:
	uvicorn main:app --reload

test:
	pytest

up:
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f api
