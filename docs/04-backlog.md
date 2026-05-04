# Backlog

## Epics

| Epic | Description | Milestone | Notes |
|------|-------------|-----------|-------|
| E1 | Repo and local dev stack | M1 | Prerequisite to everything |
| E2 | Database schema and migrations | M2 | Prerequisite to E3 and E4 |
| E3 | Authentication (+ auth tests) | M2 | Tests written alongside stories |
| E4 | Document ingestion pipeline (+ ingest tests) | M3 | Tests written alongside stories |
| E5 | RAG agent and query flow (+ query tests) | M4 | Tests written alongside stories |
| E6 | Frontend | M5 | |
| E7 | CI and final test coverage | M6 | CI setup + coverage gaps only — tests were written in E3–E5 |
| E8 | CD workflow skeleton | M6 | Write now, enable at M8 |
| E9 | Infrastructure as code | M7 | Can start in parallel once M4 done |
| E10 | Deployment | M8 | After all milestones green |

---

## Stories

### E1 — Repo and local dev stack (M1)

**US-1.1: docker-compose skeleton**
As a developer, I want a working docker-compose setup, so that the full local stack starts with one command.
- Given `make up` is run, then the `db`, `ollama`, `app`, and `migrate` services start without errors
- Given `curl localhost:8000/health`, then the response is `{"status": "ok"}`
- Given `make test`, then a placeholder test passes

**US-1.2: FastAPI app skeleton with health endpoints**
As a developer, I want `/health` and `/ready` endpoints, so that liveness and readiness can be verified.
- Given the app is running, `GET /health` returns `{"status": "ok"}` with HTTP 200
- Given the db and Ollama are reachable, `GET /ready` returns `{"status": "ok", "db": "up", "ollama": "up"}`
- Given the db is unreachable, `GET /ready` returns HTTP 503

**US-1.3: Makefile with developer commands**
As a developer, I want a Makefile, so that I don't have to remember docker-compose commands.
- `make up` — starts the full stack
- `make down` — stops it
- `make migrate` — runs alembic migrations
- `make pull-models` — pulls Ollama models into the named volume
- `make test` — runs pytest inside the app container
- `make lint` — runs ruff check
- `make fmt` — runs ruff format
- `make typecheck` — runs mypy
- `make shell` — opens a bash shell inside the app container

**US-1.4: Project configuration files**
As a developer, I want all project config committed, so that a fresh clone is immediately usable.
- `.env.example` committed with all required variable names and placeholder values
- `.env` is gitignored
- `.gitignore` covers `.env`, `__pycache__`, `.mypy_cache`, `*.pyc`, `ollama_models/`
- `.dockerignore` covers `.env`, `__pycache__`, `.git`
- `pyproject.toml` with all Poetry dependency groups

---

### E2 — Database schema and migrations (M2)

**US-2.1: SQLAlchemy models**
As a developer, I want SQLAlchemy 2.0 mapped classes for all tables, so that the ORM matches the schema.
- Models exist for `User`, `Document`, `Chunk`, `QueryHistory`
- `Chunk.embedding` is typed as `Vector(768)` using the pgvector SQLAlchemy type
- All foreign keys have cascade delete configured

**US-2.2: Alembic setup with async engine**
As a developer, I want Alembic configured for async SQLAlchemy, so that migrations run inside docker-compose.
- `alembic.ini` points to the correct migration directory
- `app/db/migrations/env.py` uses the async engine pattern
- `make migrate` runs `alembic upgrade head` successfully

**US-2.3: Initial migration**
As a developer, I want the first migration to create the full schema, so that the database is ready for use.
- Migration creates: `CREATE EXTENSION IF NOT EXISTS vector`
- Creates all four tables with correct columns, types, and constraints
- Creates the `ivfflat` index on `chunks.embedding`
- Creates B-tree indexes on all `user_id` and `document_id` columns
- Migration is reversible (downgrade defined)

**US-2.4: Async DB session factory**
As a developer, I want an async session factory, so that routes can get a DB session via dependency injection.
- `app/db/session.py` exports `get_db` as an async generator
- Engine uses `asyncpg` driver with the `DATABASE_URL` from settings

---

### E3 — Authentication (M2)

> Tests are written alongside each story here, not deferred to M6.

**US-3.1: Password hashing service + unit tests**
As the system, I want to hash and verify passwords securely, so that plaintext passwords are never stored.
- `auth_service.hash_password(plain)` returns a bcrypt hash
- `auth_service.verify_password(plain, hashed)` returns True/False
- Unit tests: correct password verifies, wrong password does not, two hashes of the same input differ

**US-3.2: JWT mint and decode service + unit tests**
As the system, I want to create and validate JWTs, so that stateless authentication is possible.
- `auth_service.create_access_token(user_id)` returns a signed JWT with 15-min expiry
- `auth_service.create_refresh_token(user_id)` returns a signed JWT with 7-day expiry
- `auth_service.decode_token(token)` returns the payload or raises on invalid/expired
- Unit tests: valid token decodes correctly, expired token raises, tampered token raises

**US-3.3: Register, login, logout, and refresh routes**
As a new user, I want to register and log in, so that I have an authenticated session.
- `POST /auth/register` creates a user, hashes the password, returns `{id, email}`; returns 409 if email already exists
- `POST /auth/login` verifies credentials, sets `access_token` and `refresh_token` HTTP-only cookies; returns 401 on wrong credentials
- `POST /auth/logout` clears both cookies; returns 204
- `POST /auth/refresh` validates the refresh token cookie, issues a new access token cookie; returns 401 on invalid token

**US-3.4: get_current_user dependency + integration tests**
As the system, I want a FastAPI dependency that extracts the authenticated user, so that protected routes never run without a valid user.
- `get_current_user` reads the `access_token` cookie, decodes the JWT, returns the `User` ORM object
- Returns 401 if cookie is missing, token is expired, or token is invalid
- Integration tests: register → login → protected route → 200; wrong password → 401; no cookie → 401; expired token → 401

---

### E4 — Document ingestion pipeline (M3)

> Tests are written alongside each story here, not deferred to M6.

**US-4.1: File parsers**
As the system, I want to extract plain text from uploaded files, so that they can be chunked and embedded.
- `parsers.parse(file_bytes, file_type)` returns a plain text string
- Supports: PDF (pypdf), DOCX (python-docx), TXT, MD
- Unsupported file type raises a clear error

**US-4.2: Text chunker + unit tests**
As the system, I want to split text into overlapping chunks, so that relevant passages can be retrieved individually.
- `chunker.chunk(text)` returns a list of strings using `RecursiveCharacterTextSplitter(chunk_size=512, chunk_overlap=50)`
- Unit tests: overlap boundary respected (600-char input → 2 chunks with 50 shared chars), very short text → one chunk, empty string → empty list

**US-4.3: Embedding provider abstraction**
As the system, I want to embed text via a swappable provider, so that Ollama and OpenAI produce compatible vectors.
- `embeddings.get_embeddings()` returns a LangChain embeddings instance based on `LLM_PROVIDER`
- Startup assertion: `assert len(model.embed_query("test")) == 768`
- Ollama provider uses `nomic-embed-text`; OpenAI provider passes `dimensions=768`

**US-4.4: Vector store persistence**
As the system, I want to store and search chunk embeddings in pgvector, so that relevant chunks can be retrieved.
- `vector_store.similarity_search(embedding, user_id, top_k)` runs cosine distance query scoped to `user_id`
- Returns list of `{id, content, document_id, chunk_index, similarity}`
- `vector_store.bulk_insert_chunks(chunks)` persists a batch of embedded chunks

**US-4.5: Upload endpoint + integration tests**
As a registered user, I want to upload a document, so that it is processed and ready for questioning.
- `POST /documents/upload` accepts `multipart/form-data`
- Validates file extension and magic bytes; rejects unsupported types with 415
- Rejects files over 50MB with 413
- Runs parse → chunk → embed → persist synchronously
- Sets document `status` to `ready` on success, `failed` on error
- Integration tests: upload fixture PDF → status `ready` → chunks persisted with correct `user_id`; unsupported type → 415; oversized file → 413

**US-4.6: List and delete documents**
As a registered user, I want to see and remove my documents, so that I can manage my knowledge base.
- `GET /documents` returns the authenticated user's documents ordered by `created_at` desc
- `DELETE /documents/{id}` deletes the document and cascades to its chunks; returns 403 if the document belongs to another user

**US-4.7: User isolation integration test**
As the system, I want a test that proves one user cannot see another's data, so that isolation bugs are caught before merge.
- User A uploads a document
- User B queries with a question that would match User A's document
- User B receives zero results in sources
- **This test must pass on every PR. A failure is a security bug, not a test failure.**

---

### E5 — RAG agent and query flow (M4)

> Tests are written alongside each story here, not deferred to M6.

**US-5.1: LLM factory**
As the system, I want a factory that returns the correct LangChain chat model, so that the agent works with either provider.
- `llm.get_chat_model()` returns `ChatOllama` or `ChatOpenAI` based on `LLM_PROVIDER`
- `ChatOllama` uses `OLLAMA_HOST` and `OLLAMA_CHAT_MODEL` from settings
- `ChatOpenAI` uses `OPENAI_API_KEY` and defaults to `gpt-4o`

**US-5.2: retrieve_tool + unit test**
As the system, I want a retrieval tool scoped to the current user, so that the agent can only access the authenticated user's chunks.
- `make_retrieve_tool(user_id, db)` returns a `@tool` function that embeds the query and calls `similarity_search`
- `user_id` is closed over — it is not in the tool's input schema
- Unit test: tool returns correctly shaped results with a mocked vector store

**US-5.3: web_search_tool + unit test**
As the system, I want an optional web search tool, so that the agent can supplement document context when enabled.
- `web_search_tool(query)` calls Tavily if `TAVILY_API_KEY` is set
- If key is unset, returns `{"status": "disabled"}` — agent skips it gracefully
- Unit test: disabled stub returns correct shape

**US-5.4: clarify_tool + unit test**
As the system, I want a clarification tool, so that the agent can ask for more detail on ambiguous questions.
- `clarify_tool(question_to_user)` returns a structured clarification request and short-circuits the agent loop
- Unit test: clarify_tool returns expected shape

**US-5.5: LangGraph agent**
As the system, I want a LangGraph ReAct agent, so that the query flow can reason, retrieve, and loop.
- `build_agent(user_id, db)` returns a compiled LangGraph agent with all three tools
- Agent is initialised with a system prompt that instructs it to ground answers in document context
- `max_iterations` guard is set (default 10) to prevent infinite loops

**US-5.6: Query service**
As the system, I want a query service, so that the endpoint can invoke the agent and return a structured response.
- `query_service.run(question, use_web_search, user_id, db)` invokes the agent
- Extracts sources from the tool call trace (not from LLM text output)
- Persists a `QueryHistory` record
- Returns `{answer, sources, used_web_search}`

**US-5.7: Query endpoint + integration tests**
As a registered user, I want to ask a question and get a cited answer, so that I can query my knowledge base.
- `POST /query` accepts `{question, use_web_search?}`
- Returns `{answer, sources: [{document, chunk_index, excerpt}], used_web_search}`
- Returns 400 if question is empty
- Integration tests: upload fixture doc → ask question → non-empty answer with at least one source; LLM is mocked via dependency injection (do not call real Ollama in integration tests)

---

### E6 — Frontend (M5)

**US-6.1: Base template and static files**
As a developer, I want Jinja2 templates mounted in FastAPI, so that the app serves HTML pages.
- `app.mount("/static", ...)` serves CSS and JS
- `base.html` includes the nav bar, static file links, and block placeholders
- `make up` serves the frontend at `http://localhost:8000`

**US-6.2: Login and register pages**
As a new user, I want login and register forms, so that I can create an account and log in.
- `GET /` redirects to `/login` if no valid cookie
- `POST` on the login form calls `/auth/login`; on success redirects to `/dashboard`
- `POST` on the register form calls `/auth/register`; on success redirects to `/login`
- Invalid credentials show an inline error message

**US-6.3: Dashboard — document management**
As a registered user, I want to upload and manage documents from the dashboard, so that I can build my knowledge base.
- Dashboard shows the user's document list (name, date, status)
- Upload form accepts file selection and submits to `/documents/upload`
- Each document has a delete button that calls `DELETE /documents/{id}`
- Page refreshes the list after upload or delete without a full page reload

**US-6.4: Query panel**
As a registered user, I want a query form and answer panel, so that I can ask questions and see cited answers.
- Query form on the dashboard submits to `POST /query`
- Answer panel displays the answer text
- Sources are listed below the answer with document name and excerpt
- Web search toggle maps to `use_web_search` in the request body

**US-6.5: Auth handling in JS**
As the system, I want the JS to handle 401 responses, so that expired sessions redirect to login automatically.
- All fetch calls check for 401 and redirect to `/login`
- No JWT is stored or read in JS — the HTTP-only cookie is handled by the browser

---

### E7 — CI and final test coverage (M6)

> Tests for each feature were written in E3–E5. This epic is for CI setup and verifying nothing was missed.

**US-7.1: GitHub Actions CI workflow**
As a developer, I want CI to run on every PR, so that broken code cannot be merged.
- `.github/workflows/ci.yaml` triggers on pull requests to `main`
- Steps: checkout → build Docker image (cached) → start pgvector container → run migrations → ruff check → mypy → pytest
- Ollama is not started in CI — LLM calls are mocked
- Workflow fails fast on any red step

**US-7.2: Branch protection on main**
As a developer, I want main protected, so that no commit bypasses CI.
- Require status checks to pass before merging
- Require at least 1 approval (self-review is acceptable when solo)
- Require linear history (no merge commits)

**US-7.3: Full coverage verification**
As a developer, I want to confirm all acceptance criteria have a corresponding test, so that nothing from the PRD slips through.
- Every Given/When/Then from E3, E4, E5 user stories has a passing test
- `make test`, `make lint`, `make typecheck` all exit 0
- User isolation test (US-4.7) is confirmed in the suite

---

### E8 — CD workflow skeleton (M6)

**US-8.1: CD workflow skeleton**
As a developer, I want a CD workflow file committed now, so that it can be enabled when AWS is ready.
- `.github/workflows/cd.yaml` triggers on push to `main`
- Steps: build → tag with commit SHA → push to ECR → `kubectl set image` → wait for rollout → smoke test `/health`
- Uses placeholder ARN and cluster values — workflow is valid YAML but a no-op until AWS is wired up
- Writing it now catches auth/OIDC/ARN misconfiguration early, before deployment pressure

---

### E9 — Infrastructure as code (M7)

> Can be started in parallel once M4 is done. Does not depend on E6, E7, or E8.

**US-9.1 to US-9.5: Terraform modules**
- `infra/terraform/modules/vpc` — VPC, subnets, route tables, NAT gateway
- `infra/terraform/modules/rds` — RDS PostgreSQL with pgvector, private subnet, security group
- `infra/terraform/modules/ecr` — ECR repository with lifecycle policy
- `infra/terraform/modules/eks` — EKS cluster, managed node group (t3.medium)
- `infra/terraform/modules/secrets` — AWS Secrets Manager entries for JWT_SECRET, OPENAI_API_KEY, DATABASE_URL
- `terraform plan` exits 0 — no `apply` yet

**US-9.6: Kubernetes manifests**
- `namespace.yaml`, `deployment.yaml` (2 replicas, readiness probe on `/ready`), `service.yaml`, `ingress.yaml` (ALB ingress class), `hpa.yaml` (scale 2–5 on CPU 70%), `configmap.yaml`, `secrets.yaml`
- `kubectl apply --dry-run=client -f infra/k8s/` exits 0

---

### E10 — Deployment (M8)

**US-10.1 to US-10.7: Full deployment**
- AWS credentials configured + OIDC trust for GitHub Actions
- `terraform apply` — provision all infra
- First manual ECR push + `kubectl apply -f infra/k8s/`
- Migration against prod DB: `kubectl exec -it deploy/rag-api -- alembic upgrade head`
- Smoke test the public ALB URL
- Enable CD workflow — auto-deploy is now active
- Write `docs/05-runbook.md`

---

## Dependency Graph

```
E1 (dev stack, M1)
│
├── E2 (schema, M2)
│   ├── E3 (auth + auth tests, M2)
│   │   ├── E4 (ingestion + ingest tests, M3)
│   │   │   └── E5 (RAG agent + query tests, M4)
│   │   │       ├── E6 (frontend, M5)
│   │   │       │   └── E7 (CI + coverage, M6)
│   │   │       │       └── E8 (CD skeleton, M6)
│   │   │       │           └── E10 (deploy, M8)
│   │   │       └── E9 (IaC written-only, M7) ← can be started in parallel once M4 is done
│   │   └── E6 (frontend, M5)
│   └── E4 (ingestion, M3)
```

**Flow:**
- E1 must be done before anything else
- E2 before E3 and E4
- E3 before any protected routes in E4, E5, E6
- E4 before E5
- E5 before E6
- E7 and E8 after E5; CD skeleton should be written by M6
- E9 can run in parallel with E6/E7/E8 once M4 is done
- E10 after everything else is ready

---

## Milestones with Definition of Done

| Milestone | Epics | Due | Definition of done |
|-----------|-------|-----|--------------------|
| **M1 — Walking skeleton** | E1 | ~3 May | `make up` starts cleanly, `GET /health` returns 200, one placeholder test passes. Zero features. |
| **M2 — Schema and auth** | E2, E3 | ~10 May | Register, login, protected route, logout all work. Auth unit + integration tests pass. Migrations clean. |
| **M3 — Ingestion** | E4 | ~17 May | Upload a PDF, see it listed, confirm chunks persisted with correct `user_id`. Ingest + user isolation tests pass. |
| **M4 — RAG query** | E5 | ~24 May | Ask a question about an uploaded document, receive a cited answer via Ollama. Query integration tests pass with mocked LLM. |
| **M5 — Frontend** | E6 | ~31 May | Full flow works in a browser: register → login → upload → query → see citations. |
| **M6 — Tests and CI** | E7, E8 | ~31 May | `make test` green, `make lint` clean, `make typecheck` clean. CI green on every PR. CD skeleton committed. All acceptance criteria from E3–E5 have a passing test. |
| **M7 — Infra as code** | E9 | ~7 Jun | `terraform plan` exits 0, `kubectl apply --dry-run` exits 0. No AWS resources created yet. |
| **M8 — Deployed** | E10 | ~Jun 8+ | App reachable at a public URL. Runbook written. CD workflow enabled. |
