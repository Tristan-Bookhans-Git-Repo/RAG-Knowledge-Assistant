import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.config import settings
from app.db.session import engine
from app.routers.auth import router as auth_router
from app.routers.documents import router as documents_router
from app.routers.query import router as query_router
from app.services.embeddings import get_embeddings, validate_embedding_dim
from app.templating import templates

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    validate_embedding_dim(get_embeddings())
    yield
    await engine.dispose()


app = FastAPI(title="RAG Knowledge Assistant", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")
app.include_router(auth_router)
app.include_router(documents_router)
app.include_router(query_router)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "index.html")


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
