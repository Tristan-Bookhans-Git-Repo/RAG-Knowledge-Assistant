from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.config import settings
from app.db.session import get_db
from app.main import app


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
