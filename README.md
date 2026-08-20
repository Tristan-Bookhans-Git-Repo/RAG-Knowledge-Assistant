# RAG Knowledge Assistant

A multi-user retrieval-augmented generation (RAG) assistant with per-user data isolation. Upload your documents, ask questions, get answers grounded in your own content with citations back to the source. I built this to work through the full stack of an LLM application end to end: ingestion, vector retrieval, a tool-using agent, and a cited answer, not just a wrapper around a chat API.

> **Status:** personal project, in active development. Backend (auth, ingestion, retrieval, agent, query flow) and frontend are built and tested. CI runs on every push. Infrastructure as code (Terraform, Kubernetes manifests) is written and plan-validated but not yet applied to real AWS. See [Status & roadmap](#status--roadmap).

## What it does

- Upload PDF, DOCX, TXT or Markdown documents.
- Each document is parsed, chunked, embedded, and stored per user in a pgvector store.
- Ask a question and a tool-using agent retrieves the most relevant passages from your own documents only, grounds its answer in them, and returns citations (source document + chunk).
- The agent can ask a clarifying question when a query is ambiguous, and optionally fall back to web search when the answer isn't in your documents.

## Architecture

**Ingestion.** `POST /documents/upload`. `parse` (PDF / DOCX / TXT / MD) → `chunk` (recursive, 512 chars / 50 overlap) → `embed` (768-dim) → store in Postgres + pgvector. Uploads are validated by extension, size (50 MB) and magic bytes; each document carries a `processing → ready / failed` status, and a failed parse rolls back cleanly.

**Retrieval and query.** `POST /query`. Each request builds a per-request agent whose retrieval tool has the caller's `user_id` bound into the query in server code. It's never exposed to the model, so a user's agent can only ever reach that user's chunks. Retrieval is cosine similarity over pgvector (top-k). The agent (LangChain `create_agent`, LangGraph-based, ReAct-style) gets three tools:

- `retrieve`: similarity search over the user's own documents (the isolation boundary)
- `clarify`: ask the user a question when the query is ambiguous
- `web_search`: optional Tavily fallback, only when the answer isn't in the documents

The query service streams the agent run, extracts the retrieved passages as structured sources, records the query, and returns the answer plus citations (filename, chunk index, text).

**Providers.** LLM and embeddings sit behind a small provider abstraction: OpenAI (`gpt-4o`, `text-embedding-3-small`) or local Ollama (`qwen2.5:7b`, `nomic-embed-text`), swappable via config without touching the rest of the system. Note: `llama3.2` was the original local default and doesn't reliably emit structured tool calls through Ollama, which silently broke retrieval. Switched to `qwen2.5:7b` after finding and reproducing that (see ADR-006).

## Key design decisions

- **Per-user isolation as a hard boundary.** The `user_id` is bound into the retrieval query on the server, not passed to the LLM, so no prompt can talk the agent into another user's data. Covered by an integration test asserting that user B's search returns none of user A's chunks (`tests/integration/test_vector_store.py`), plus an end-to-end version through the actual `/query` endpoint.
- **Structured sources across the tool boundary.** The retrieve tool returns `content_and_artifact`, so the raw results (with their IDs) survive alongside the text the model reasons over. Citations are exact, not re-parsed from prose.
- **Defensive ingestion.** Type, size, and magic-byte validation, plus a per-document status with rollback, so a bad upload fails cleanly instead of corrupting the store.
- **Provider-agnostic by default.** Runs fully locally on Ollama with no API keys, or on OpenAI by flipping one setting.
- **HttpOnly cookies for the browser, Bearer tokens for the API.** The frontend never touches a JWT directly; `get_current_user` accepts either, so the same endpoints serve both without duplicating auth logic.

## Tech stack

Python, FastAPI, LangChain / LangGraph agents, PostgreSQL + pgvector, SQLAlchemy (async) + Alembic, JWT auth, Jinja2 frontend, Docker / docker-compose, pytest (100% line coverage), GitHub Actions CI, Terraform (AWS: VPC, RDS, EKS, ECR, Secrets Manager, written and plan-validated, not yet applied).

## API

| Method | Path | Purpose |
|---|---|---|
| POST | `/auth/register`, `/auth/login`, `/auth/logout`, `/auth/refresh` | JWT auth (access + refresh) |
| POST | `/documents/upload` | Upload and ingest a document |
| GET | `/documents` | List your documents |
| DELETE | `/documents/{id}` | Delete a document (and its chunks) |
| POST | `/query` | Ask a question, get a cited answer |
| GET | `/health`, `/ready` | Liveness + readiness (DB + Ollama) |

There's also a server-rendered frontend (login, register, dashboard with upload/list/delete, query panel) at `/`, `/login`, `/register`, `/dashboard`.

## Running locally

```bash
docker compose up
```

Brings up the API, Postgres + pgvector, and Ollama. On first run, pull the models (`qwen2.5:7b`, `nomic-embed-text`). Configuration lives in `.env` (see `.env.example`); it runs on Ollama with no external keys by default. Database schema is managed with Alembic migrations.

## Testing

```bash
pytest
```

100% line coverage, 163 tests, passing with Ollama fully stopped (CI never runs it, so the whole test suite has to work without it). Unit tests cover the parsers, chunker, embedding/LLM factories, each agent tool, the agent builder, and the query service, with the LLM mocked. Integration tests cover auth, document upload, the query endpoint, the frontend routes, and the vector store, including the per-user isolation boundary.

## Status & roadmap

**Built and tested:** JWT auth (cookie + Bearer); the full ingestion pipeline; per-user vector storage and retrieval; the tool-using agent; the cited-answer query flow; server-rendered frontend; CI on every push.

**Known limitations / what's next:**

- **Retrieval quality.** Currently top-k by cosine similarity, no relevance threshold, reranking, or hybrid (keyword + vector) search. A tuned similarity floor and reranking are next.
- **Evaluation.** No automated eval harness yet; retrieval quality is checked via the test suite and manual spot-checks. A labelled golden set with recall@k and answer-faithfulness metrics is designed but not built.
- **Grounding.** The system prompt grounds answers in the retrieved passages and cites them; an explicit "refuse when the answer isn't present" instruction is a small pending addition.
- **Conversation.** Single-turn today, each query is independent. Multi-turn memory (LangGraph checkpointer + thread ID) is designed but not built, since a clarifying question currently can't carry context into the next query.
- **Deployment.** Terraform modules for VPC, RDS, EKS, ECR, and Secrets Manager are written and `terraform plan` clean, but nothing has been applied to real AWS yet. CD workflow is a valid, no-op skeleton (build, push to ECR, `kubectl set image`, health check) waiting on that infrastructure to exist.
