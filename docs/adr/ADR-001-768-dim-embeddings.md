# ADR-001: Standardise on 768-dimensional embeddings

**Date:** 2026-04-29
**Status:** Validated

## Context

The application stores vector embeddings in a pgvector column and will support two LLM providers:
- **Ollama** (local): `nomic-embed-text` natively outputs 768-dimensional vectors
- **OpenAI** (hosted): `text-embedding-3-small` defaults to 1536 dimensions but supports a `dimensions=768` truncation parameter
- Will validate other LLM's at a later point to verify how results differ. 

If the two providers produce embeddings of different dimensions, the `vector(N)` column definition in PostgreSQL would need to change when switching providers. That means a schema migration and a full reindex of all stored chunks which would be expensive and error-prone in production.

## Decision

Fix the pgvector column at `vector(768)` and configure both providers to output exactly 768 dimensions:
- Ollama `nomic-embed-text` → 768 natively, no configuration needed
- OpenAI `text-embedding-3-small` → pass `dimensions=768` in the API call

Add a startup assertion in the RAG embedding implementation file:
```python
assert len(model.embed_query("test")) == 768, "Embedding dim mismatch"
```
This fails fast at boot rather than silently storing incompatible vectors.

## Consequences

- Switching between Ollama and OpenAI requires only changing `LLM_PROVIDER` in `.env`. No schema change, no reindex
- 768 dimensions is slightly lower precision than OpenAI's 1536-dim default, but adequate for document retrieval at this scale
- If a future embedding model does not support 768-dim output, a migration and full reindex would be required — this is acceptable as a known future cost
