from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_user_from_cookie
from app.models.document import Document
from app.models.user import User
from app.templating import templates

router = APIRouter()


@router.get("/")
async def index(
    current_user: User | None = Depends(get_current_user_from_cookie),
) -> RedirectResponse:
    if current_user is None:
        return RedirectResponse(url="/login")
    return RedirectResponse(url="/dashboard")


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "login.html")


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "register.html")


@router.get("/dashboard")
async def dashboard_page(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_from_cookie),
) -> Response:
    if current_user is None:
        return RedirectResponse(url="/login")

    result = await db.execute(
        select(Document)
        .where(Document.user_id == current_user.id)
        .order_by(Document.created_at.desc())
    )
    documents = result.scalars().all()

    return templates.TemplateResponse(request, "dashboard.html", {"documents": documents})
