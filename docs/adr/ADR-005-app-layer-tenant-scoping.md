# ADR-005: Application-layer user scoping

**Date:** 2026-05-02
**Status:** Validated

## Context

Multiple users share a single PostgreSQL database. A core security requirement (from the PRD) is that a user's query must never return document chunks belonging to another user.

Two approaches to enforce this:

| Approach | Where enforced | Bypass risk |
|----------|---------------|-------------|
| **Application layer** — `WHERE user_id = :uid` in every query | App code | A bug in app code could omit the filter |
| **Postgres Row Level Security (RLS)** | Database | Cannot be bypassed by app code bugs |

RLS is the stronger defence because it enforces the boundary at the database level regardless of what the application sends. However, it requires:
- Configuring RLS policies for each table
- Passing the authenticated user's ID to PostgreSQL as a session variable on every connection
- Careful interaction with SQLAlchemy's connection pool (session variables must be reset between connections)
- Additional complexity in the migration and the ORM setup

For v1, the affects a user isolation bug is limited: this is a self-hosted personal project, not a multi-user application. The complexity cost of RLS is not justified at this stage.

## Decision

Enforce user isolation at the application layer:

1. `get_current_user` (FastAPI dependency) extracts `user_id` from the JWT cookie — never from the request body
2. `build_agent(user_id, db)` constructs `retrieve_tool` as a closure over `user_id`:
   ```python
   def make_retrieve_tool(user_id: uuid.UUID, db: AsyncSession):
       @tool
       async def retrieve_tool(query: str) -> list[dict]:
           embedding = await embed(query)
           return await similarity_search(embedding, user_id, db)
       return retrieve_tool
   ```
3. `user_id` is **not** in the tool's input schema — the LLM cannot pass or override it
4. Every raw SQL query in will include `WHERE user_id = :user_id`

A user isolation integration test will be the primary guard:
- User A uploads a document
- User B queries — expects zero results from User A's document
- This test must pass on every PR

## Consequences

- Simple, readable, testable — the isolation logic will be explicit in the code
- A future code change that accidentally removes a `WHERE user_id` clause could break isolation — the integration test catches this
- Postgres RLS is explicitly noted as a v2 hardening option — adding it later does not require changing the application logic, only adding policies and adjusting the session setup
- This approach is consistent with how most application-layer multi-tenancy is implemented at this scale
