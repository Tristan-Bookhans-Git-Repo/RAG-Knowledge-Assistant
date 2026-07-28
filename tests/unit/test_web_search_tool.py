from unittest.mock import MagicMock, patch

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


def test_web_search_tool_calls_tavily_when_key_set(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "TAVILY_API_KEY", "fake-key")
    fake_results = [{"title": "Result", "url": "https://example.com"}]

    mock_instance = MagicMock()
    mock_instance.invoke.return_value = fake_results
    mock_tavily_class = MagicMock(return_value=mock_instance)

    with patch("langchain_tavily.TavilySearch", mock_tavily_class):
        result = web_search_tool.invoke({"query": "what is RAG?"})

    assert result == fake_results
    mock_tavily_class.assert_called_once_with(max_results=5)
    mock_instance.invoke.assert_called_once_with({"query": "what is RAG?"})
