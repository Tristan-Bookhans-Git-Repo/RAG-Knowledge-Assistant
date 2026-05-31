# Contributing

## Prerequisites

- Docker Desktop
- Git

No Python, Node, or other tools need to be installed on the host. Everything runs inside containers.

---

## Local dev setup

```bash
cp .env.example .env           # fill in any secrets you need locally
make up                        # builds images and starts db, ollama, app
make migrate                   # runs alembic upgrade head
make pull-models               # downloads nomic-embed-text and llama3.2 into the ollama volume
```

The app reloads automatically on file changes (uvicorn `--reload` + volume mount).

---

## Daily commands

| Command | What it does |
|---|---|
| `make up` | Build images and start all services |
| `make down` | Stop and remove containers |
| `make migrate` | Run pending Alembic migrations |
| `make test` | Run the full pytest suite inside the app container |
| `make lint` | Run ruff check (linting) |
| `make fmt` | Run ruff format (formatting) |
| `make typecheck` | Run mypy strict type check |
| `make shell` | Open a bash shell inside the app container |

Run lint, format, and tests before every push:

```bash
make lint && make fmt && make test
```

---

## Database migrations

### Applying migrations

```bash
make migrate
```

Run this after cloning, after pulling a branch that added a migration, and in CI before tests.

### Creating a migration

Only needed when you change a model (add/remove a table or column). Run inside the app container so it can compare your models against the live database:

```bash
docker compose exec app alembic revision --autogenerate -m "short description of change"
```

This generates a file in `app/db/migrations/versions/`. **Always review it before applying**.

```bash
docker compose build migrate
make migrate
```

### Rolling back

```bash
docker compose exec app alembic downgrade base    # undo all migrations
docker compose exec app alembic downgrade -1      # undo only the most recent
```

---

## Branch naming

```
feature/<epic_number>-<short_description>
story/<story_number>-<short-description>
bug/<story_number>-<short-description>
chore/<short-description>
```

Examples:

```
feature/7-Repo_dev_stack_setup
story/20-Project_config_files
bug/33-Add_missing_import
chore/update-dependencies
```

---

## Commit messages

Based of [Conventional Commits](https://www.conventionalcommits.org/) but a bit more detail in the commit message:

commit message:
```
<type of issue><issue number> - <short summary of changes>
```

commit description:
```
List of changes using bullet points
```

**Types:**

| Type | When to use |
|---|---|
| `feature` | New feature or behaviour |
| `US` | Small code changes part of a feature |
| `bug` | Bug fix |
| `chore` | Tooling, dependencies, config — no production code change |
| `docs` | Documentation only |
| `test` | Adding or fixing tests |
| `refactor` | Code change that neither fixes a bug nor adds a feature |
| `ci` | CI/CD pipeline changes |

**Examples:**

```
feature7 - Repo and local dev stack
US19 - Add dev commands to make file and added alembic setup files
bug23 - handle zero-byte PDF uploads
chore45 - bump langchain to 1.2.18
test67 - add tenant isolation assertion
docs34 - update CONTRIBUTING with branch naming
```

Rules:
- Summary is lowercase, present tense, no trailing period
- Body is optional

---

## Code style

Enforced automatically by ruff and mypy (run via `make lint`, `make fmt`, `make typecheck`):

- **Line length:** 100 characters
- **Formatter:** ruff format (Black-compatible)
- **Linter:** ruff with E, F, I (isort), UP (pyupgrade) rule sets
- **Type checking:** mypy strict mode, Python 3.11
- **No `# type: ignore`** unless accompanied by a comment explaining why

---

## Pull requests

- One story per PR where possible (Except feature PRs to `Main`)
- PR title follows the same conventional commit format as commits
- Fill in the PR template: description, test plan
- All checks must pass before merge (lint, typecheck, tests)
- Squash-merge to keep history linear
