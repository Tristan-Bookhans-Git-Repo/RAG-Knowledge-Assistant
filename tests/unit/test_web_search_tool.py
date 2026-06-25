import pytest

from app.config import settings
from app.services.web_search_tool import web_search_tool


def test_web_search_tool_returns_disabled_when_key_unset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "TAVILY_API_KEY", "")
    result = web_search_tool.invoke({"query": "anything"})
    assert result == {"status": "disabled"}


def test_web_search_tool_has_query_in_schema() -> None:
    assert "query" in web_search_tool.args
