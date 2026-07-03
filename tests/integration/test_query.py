import io
import uuid
from collections.abc import AsyncGenerator
from typing import Any

import pytest
from fpdf import FPDF
from httpx import ASGITransport, AsyncClient
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.config import settings
from app.db.session import get_db
from app.dependencies import get_llm
from app.main import app


class _FakeRAGModel(BaseChatModel):
    """Fake LLM for integration tests.

    First call (no ToolMessage in history): invokes the retrieve tool
    using the user's question as the query.

    Second call (ToolMessage present): returns a fixed final answer so
    the agent loop terminates.

    This lets the real retrieve tool run against the real DB, meaning
    isolation and chunk-presence tests reflect actual DB state.
    """

    @property
    def _llm_type(self) -> str:
        return "fake-rag"

    def bind_tools(self, tools: Any, **kwargs: Any) -> "_FakeRAGModel":
        # create_agent calls bind_tools() to register tool schemas with the
        # model. This fake always emits the same fixed tool call regardless
        # of the schemas passed in, so binding is a no-op.
        return self

    def _respond(self, messages: list[BaseMessage]) -> AIMessage:
        if any(isinstance(m, ToolMessage) for m in messages):
            return AIMessage(content="Answer from your documents.")
        question = next(
            (m.content for m in reversed(messages) if isinstance(m, HumanMessage)),
            "query",
        )
        return AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "retrieve",
                    "args": {"query": str(question)},
                    "id": "tc_001",
                    "type": "tool_call",
                }
            ],
        )

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        return ChatResult(generations=[ChatGeneration(message=self._respond(messages))])

    async def _agenerate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        return ChatResult(generations=[ChatGeneration(message=self._respond(messages))])


@pytest.fixture
async def query_client() -> AsyncGenerator[AsyncClient, None]:
    test_engine = create_async_engine(settings.DATABASE_URL, poolclass=NullPool)
    TestSession = async_sessionmaker(test_engine, expire_on_commit=False)

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with TestSession() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise

    def override_get_llm() -> BaseChatModel:
        return _FakeRAGModel()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_llm] = override_get_llm

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()
    await test_engine.dispose()


def unique_email() -> str:
    return f"query_{uuid.uuid4().hex[:8]}@example.com"


def _make_pdf(content: str) -> bytes:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.cell(text=content)
    buf = io.BytesIO()
    pdf.output(buf)
    return buf.getvalue()


async def _register_and_token(client: AsyncClient) -> tuple[str, uuid.UUID]:
    reg = await client.post(
        "/auth/register", json={"email": unique_email(), "password": "pass1234"}
    )
    token = reg.json()["access_token"]
    me = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    return token, uuid.UUID(me.json()["id"])


async def _upload(client: AsyncClient, token: str, content: str = "Test document.") -> None:
    await client.post(
        "/documents/upload",
        files={"file": ("doc.pdf", _make_pdf(content), "application/pdf")},
        headers={"Authorization": f"Bearer {token}"},
    )


# ── success path ───────────────────────────────────────────────────────────


async def test_query_returns_200_with_answer_and_sources(
    query_client: AsyncClient,
) -> None:
    token, _ = await _register_and_token(query_client)
    await _upload(query_client, token, "RAG stands for Retrieval-Augmented Generation.")

    response = await query_client.post(
        "/query",
        json={"question": "What is RAG?"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] != ""
    assert len(body["sources"]) > 0
    assert "used_web_search" in body


async def test_query_source_fields_present(query_client: AsyncClient) -> None:
    token, _ = await _register_and_token(query_client)
    await _upload(query_client, token, "Python is a programming language.")

    response = await query_client.post(
        "/query",
        json={"question": "What is Python?"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    source = response.json()["sources"][0]
    assert "document_id" in source
    assert "chunk_index" in source
    assert "text" in source


# ── validation ─────────────────────────────────────────────────────────────


async def test_query_returns_400_for_blank_question(query_client: AsyncClient) -> None:
    token, _ = await _register_and_token(query_client)

    response = await query_client.post(
        "/query",
        json={"question": "   "},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 400


async def test_query_returns_401_without_token(query_client: AsyncClient) -> None:
    response = await query_client.post("/query", json={"question": "What is RAG?"})
    assert response.status_code == 401


# ── tenant isolation (security) ────────────────────────────────────────────


async def test_query_tenant_isolation(query_client: AsyncClient) -> None:
    """User B must never receive sources from User A's documents.

    A non-empty sources list here is a security bug — treat as P0.
    """
    token_a, _ = await _register_and_token(query_client)
    await _upload(query_client, token_a, "Confidential: the secret is 42.")

    token_b, _ = await _register_and_token(query_client)

    response = await query_client.post(
        "/query",
        json={"question": "What is the secret?"},
        headers={"Authorization": f"Bearer {token_b}"},
    )

    assert response.status_code == 200
    assert (
        response.json()["sources"] == []
    ), "SECURITY BUG: User B received sources belonging to User A"
