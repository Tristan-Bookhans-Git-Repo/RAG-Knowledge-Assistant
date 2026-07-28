from collections.abc import AsyncGenerator, Callable, Coroutine
from typing import Any
from unittest.mock import patch

import httpx
import pytest
from httpx import AsyncClient

from app.db.session import engine

_SelectiveGet = Callable[..., Coroutine[Any, Any, httpx.Response]]


@pytest.fixture(autouse=True)
async def _fresh_engine_pool() -> AsyncGenerator[None, None]:
    await engine.dispose()
    yield


def _make_selective_get(*, raise_for_ollama: bool, ollama_status_code: int = 200) -> _SelectiveGet:
    original_get = httpx.AsyncClient.get

    async def _get(self: httpx.AsyncClient, url: Any, *args: Any, **kwargs: Any) -> httpx.Response:
        if "11434" in str(url):
            if raise_for_ollama:
                raise httpx.ConnectError("connection refused")
            return httpx.Response(ollama_status_code, request=httpx.Request("GET", str(url)))
        return await original_get(self, url, *args, **kwargs)

    return _get


async def test_ready_returns_200_when_db_and_ollama_up(client: AsyncClient) -> None:
    with patch.object(httpx.AsyncClient, "get", _make_selective_get(raise_for_ollama=False)):
        response = await client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "db": "up", "ollama": "up"}


async def test_ready_returns_503_when_db_down(client: AsyncClient) -> None:
    with (
        patch("sqlalchemy.ext.asyncio.AsyncEngine.connect", side_effect=Exception("db down")),
        patch.object(httpx.AsyncClient, "get", _make_selective_get(raise_for_ollama=False)),
    ):
        response = await client.get("/ready")

    assert response.status_code == 503
    body = response.json()
    assert body["status"] == "degraded"
    assert body["db"] == "down"


async def test_ready_reports_ollama_down_on_connection_failure(client: AsyncClient) -> None:
    with patch.object(httpx.AsyncClient, "get", _make_selective_get(raise_for_ollama=True)):
        response = await client.get("/ready")

    assert response.json()["ollama"] == "down"


async def test_ready_reports_ollama_na_when_provider_is_not_ollama(client: AsyncClient) -> None:
    with patch("app.main.settings.LLM_PROVIDER", "openai"):
        response = await client.get("/ready")

    assert response.json()["ollama"] == "n/a"
