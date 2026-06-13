.PHONY: up down stop start migrate pull-models test coverage lint fmt typecheck shell

override ARGS += $(FLAGS)

up:
	docker compose up -d --build $(ARGS)

stop:
	docker compose stop $(ARGS)

start:
	docker compose start $(ARGS)

down:
	docker compose down $(ARGS)

migrate:
	docker compose --profile migrate run --rm migrate $(ARGS)

pull-models:
	docker compose exec ollama ollama pull nomic-embed-text
	docker compose exec ollama ollama pull llama3.2

test:
	docker compose exec app pytest -v $(ARGS)

coverage:
	docker compose exec app pytest -v --cov=app --cov-report=term-missing --cov-report=html:htmlcov $(ARGS)

lint:
	docker compose exec app ruff check . $(ARGS)

fmt:
	docker compose exec app ruff format . $(ARGS)

typecheck:
	docker compose exec app mypy app $(ARGS)

shell:
	docker compose exec app bash $(ARGS)
