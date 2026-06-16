import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.config import settings
from app.db.session import engine
from app.routers.auth import router as auth_router
from app.services.embeddings import get_embeddings, validate_embedding_dim

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    validate_embedding_dim(get_embeddings())
    yield
    await engine.dispose()


app = FastAPI(title="RAG Knowledge Assistant", lifespan=lifespan)
app.include_router(auth_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
async def ready() -> JSONResponse:
    db_status = "down"
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        db_status = "up"
    except Exception as exc:
        logger.warning("DB readiness check failed: %s", exc)

    ollama_status = "n/a"
    if settings.LLM_PROVIDER == "ollama":
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{settings.OLLAMA_HOST}/api/tags", timeout=3.0)
            ollama_status = "up" if resp.status_code == 200 else "down"
        except Exception as exc:
            logger.warning("Ollama readiness check failed: %s", exc)
            ollama_status = "down"

    overall = "ok" if db_status == "up" else "degraded"
    code = 200 if db_status == "up" else 503
    return JSONResponse(
        content={"status": overall, "db": db_status, "ollama": ollama_status},
        status_code=code,
    )
