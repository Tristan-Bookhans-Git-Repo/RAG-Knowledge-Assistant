from collections.abc import AsyncGenerator
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient
from langchain_core.embeddings import Embeddings
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.config import settings
from app.db.session import get_db
from app.main import app
from app.services.embeddings import get_embeddings


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    test_engine = create_async_engine(settings.DATABASE_URL, poolclass=NullPool)
    TestSession = async_sessionmaker(test_engine, expire_on_commit=False)

    async with TestSession() as session:
        yield session

    await test_engine.dispose()


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    # NullPool disables connection pooling so each test gets fresh asyncpg
    # connections within its own event loop — avoids "attached to a different
    # loop" errors when pytest-asyncio creates a new loop per test.
    test_engine = create_async_engine(settings.DATABASE_URL, poolclass=NullPool)
    TestSession = async_sessionmaker(test_engine, expire_on_commit=False)

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with TestSession() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()
    await test_engine.dispose()


def unit_vector(index: int, dim: int = settings.EMBED_DIM, sign: float = 1.0) -> list[float]:
    vec = [0.0] * dim
    vec[index] = sign
    return vec


class _FakeEmbeddingModel(Embeddings):
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [unit_vector(0) for _ in texts]

    def embed_query(self, text: str) -> list[float]:
        return unit_vector(0)


@pytest.fixture
async def embed_client() -> AsyncGenerator[AsyncClient, None]:
    test_engine = create_async_engine(settings.DATABASE_URL, poolclass=NullPool)
    TestSession = async_sessionmaker(test_engine, expire_on_commit=False)

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with TestSession() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise

    def override_get_embeddings() -> Embeddings:
        return _FakeEmbeddingModel()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_embeddings] = override_get_embeddings

    # get_embeddings() is also called directly inside retrieve_tool.py's tool
    # closure (query-time retrieval), which never goes through FastAPI's
    # Depends() graph — dependency_overrides can't reach it, so the name as
    # imported into that module needs a separate patch.
    with patch("app.services.retrieve_tool.get_embeddings", override_get_embeddings):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            yield c

    app.dependency_overrides.clear()
    await test_engine.dispose()
