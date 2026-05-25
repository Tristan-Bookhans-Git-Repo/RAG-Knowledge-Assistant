.PHONY: up down migrate pull-models test lint fmt typecheck shell

up:
	docker compose up -d --build

down:
	docker compose down

migrate:
	docker compose --profile migrate run --rm migrate

pull-models:
	docker compose exec ollama ollama pull nomic-embed-text
	docker compose exec ollama ollama pull llama3.2

test:
	docker compose exec app pytest -v

lint:
	docker compose exec app ruff check .

fmt:
	docker compose exec app ruff format .

typecheck:
	docker compose exec app mypy app

shell:
	docker compose exec app bash
