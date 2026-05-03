# ADR-002: pgvector over a dedicated vector database

**Date:** 2026-04-30
**Status:** Validated

## Context

RAG requires a vector similarity search layer to retrieve relevant document chunks. Options considered:

| Option | Type | Notes |
|--------|------|-------|
| **pgvector** | Postgres extension | Runs inside the existing PostgreSQL instance |
| **Pinecone** | Managed cloud service | No self-hosting, paid beyond free tier |
| **Weaviate** | Self-hosted or managed | Additional service to deploy and operate |
| **Qdrant** | Self-hosted or managed | Additional service to deploy and operate |

The application already requires PostgreSQL for relational data (users, documents, query_history). Adding a dedicated vector database introduces a second stateful service to run locally, deploy to production, back up, and monitor.

## Decision

Use pgvector as a PostgreSQL extension. The `chunks` table stores embeddings in a `vector(768)` column. An `ivfflat` index with `lists=100` provides approximate nearest-neighbour search adequate for this scale.

```sql
CREATE INDEX ON chunks USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

Similarity search uses cosine distance:
```sql
SELECT id, content, document_id, chunk_index,
       1 - (embedding <=> :query_embedding) AS similarity
FROM chunks
WHERE user_id = :user_id
ORDER BY embedding <=> :query_embedding
LIMIT :first_k;
```

## Consequences

- Single database for all data — one connection pool, one backup strategy, one service in docker-compose and EKS
- Joins between `chunks`, `documents`, and `users` are free and in the same DB, not cross-service calls
- `ivfflat` is approximate and requires the index to be built after bulk inserts (`VACUUM ANALYZE`) — acceptable for this use case
- At very high scale (100M+ vectors), a dedicated vector DB (Qdrant, Weaviate) would outperform pgvector — this is a known migration path if the project grows
- Pinecone was ruled out as it cannot be self-hosted, which breaks the offline/local operation use case
