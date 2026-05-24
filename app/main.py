from contextlib import asynccontextmanager
from typing import AsyncGenerator

import httpx
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.config import settings

_engine: AsyncEngine | None = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    global _engine
    _engine = create_async_engine(settings.DATABASE_URL)
    yield
    if _engine:
        await _engine.dispose()


app = FastAPI(title="RAG Knowledge Assistant", lifespan=lifespan)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
async def ready() -> JSONResponse:
    db_status = "down"
    if _engine is not None:
        try:
            async with _engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            db_status = "up"
        except Exception:
            pass

    ollama_status = "n/a"
    if settings.LLM_PROVIDER == "ollama":
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{settings.OLLAMA_HOST}/api/tags", timeout=3.0)
            ollama_status = "up" if resp.status_code == 200 else "down"
        except Exception:
            ollama_status = "down"

    overall = "ok" if db_status == "up" else "degraded"
    code = 200 if db_status == "up" else 503
    return JSONResponse(
        content={"status": overall, "db": db_status, "ollama": ollama_status},
        status_code=code,
    )
