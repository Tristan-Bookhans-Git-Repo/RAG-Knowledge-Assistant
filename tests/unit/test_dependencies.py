import uuid
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import jwt
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.config import settings
from app.dependencies import get_current_user, get_current_user_from_cookie, get_llm
from app.services.auth_service import ALGORITHM


def _token(payload: dict[str, Any]) -> str:
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=ALGORITHM)


def _credentials(token: str) -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


def _mock_request(cookie_token: str | None = None) -> MagicMock:
    request = MagicMock()
    request.cookies = {"access_token": cookie_token} if cookie_token else {}
    return request


# ── get_current_user (Bearer header) ────────────────────────────────────────


async def test_get_current_user_missing_sub_claim_returns_401() -> None:
    token = _token({"type": "access"})
    with pytest.raises(HTTPException) as exc:
        await get_current_user(_credentials(token), _mock_request(), MagicMock())
    assert exc.value.status_code == 401


async def test_get_current_user_invalid_uuid_sub_returns_401() -> None:
    token = _token({"type": "access", "sub": "not-a-uuid"})
    with pytest.raises(HTTPException) as exc:
        await get_current_user(_credentials(token), _mock_request(), MagicMock())
    assert exc.value.status_code == 401


async def test_get_current_user_unknown_user_returns_401() -> None:
    token = _token({"type": "access", "sub": str(uuid.uuid4())})
    db = MagicMock()
    db.get = AsyncMock(return_value=None)
    with pytest.raises(HTTPException) as exc:
        await get_current_user(_credentials(token), _mock_request(), db)
    assert exc.value.status_code == 401


# ── get_current_user_from_cookie ─────────────────────────────────────────────


async def test_get_current_user_from_cookie_no_token_returns_none() -> None:
    result = await get_current_user_from_cookie(_mock_request(None), MagicMock())
    assert result is None


async def test_get_current_user_from_cookie_garbage_token_returns_none() -> None:
    result = await get_current_user_from_cookie(_mock_request("garbage"), MagicMock())
    assert result is None


async def test_get_current_user_from_cookie_wrong_type_returns_none() -> None:
    token = _token({"type": "refresh", "sub": str(uuid.uuid4())})
    result = await get_current_user_from_cookie(_mock_request(token), MagicMock())
    assert result is None


async def test_get_current_user_from_cookie_missing_sub_returns_none() -> None:
    token = _token({"type": "access"})
    result = await get_current_user_from_cookie(_mock_request(token), MagicMock())
    assert result is None


async def test_get_current_user_from_cookie_invalid_uuid_returns_none() -> None:
    token = _token({"type": "access", "sub": "not-a-uuid"})
    result = await get_current_user_from_cookie(_mock_request(token), MagicMock())
    assert result is None


# ── get_llm ──────────────────────────────────────────────────────────────────


def test_get_llm_returns_chat_model() -> None:
    from langchain_core.language_models import BaseChatModel

    assert isinstance(get_llm(), BaseChatModel)
