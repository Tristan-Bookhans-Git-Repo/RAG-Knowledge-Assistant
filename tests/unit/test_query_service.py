import uuid
from collections.abc import AsyncGenerator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

from langchain_core.messages import AIMessage

from app.services.query_service import run


def _make_source() -> dict[str, Any]:
    return {
        "id": uuid.uuid4(),
        "content": "RAG stands for Retrieval-Augmented Generation.",
        "document_id": uuid.uuid4(),
        "chunk_index": 0,
        "similarity": 0.95,
    }


def _make_agent(events: list[dict[str, Any]]) -> MagicMock:
    async def _astream_events(
        *args: object, **kwargs: object
    ) -> AsyncGenerator[dict[str, Any], None]:
        for event in events:
            yield event

    agent = MagicMock()
    agent.astream_events = _astream_events
    return agent


def _final_state_event(answer: str) -> dict[str, Any]:
    return {
        "event": "on_chain_end",
        "name": "",
        "data": {"output": {"messages": [AIMessage(content=answer)]}},
    }


def _retrieve_event(sources: list[Any]) -> dict[str, Any]:
    return {"event": "on_tool_end", "name": "retrieve", "data": {"output": sources}}


def _web_search_event() -> dict[str, Any]:
    return {"event": "on_tool_end", "name": "web_search_tool", "data": {"output": []}}


def _mock_db() -> MagicMock:
    db = MagicMock()
    db.commit = AsyncMock()
    return db


async def test_run_returns_answer() -> None:
    agent = _make_agent([_final_state_event("The answer is 42.")])
    db = _mock_db()
    with patch("app.services.query_service.build_agent", return_value=agent):
        result = await run("What is the answer?", False, uuid.uuid4(), db)
    assert result["answer"] == "The answer is 42."


async def test_run_extracts_sources_from_retrieve_event() -> None:
    source = _make_source()
    agent = _make_agent([_retrieve_event([source]), _final_state_event("Answer.")])
    db = _mock_db()
    with patch("app.services.query_service.build_agent", return_value=agent):
        result = await run("What is RAG?", False, uuid.uuid4(), db)
    assert result["sources"] == [source]


async def test_run_accumulates_multiple_retrieve_calls() -> None:
    s1, s2 = _make_source(), _make_source()
    agent = _make_agent(
        [_retrieve_event([s1]), _retrieve_event([s2]), _final_state_event("Answer.")]
    )
    db = _mock_db()
    with patch("app.services.query_service.build_agent", return_value=agent):
        result = await run("What is RAG?", False, uuid.uuid4(), db)
    assert result["sources"] == [s1, s2]


async def test_run_detects_web_search_used() -> None:
    agent = _make_agent([_web_search_event(), _final_state_event("Found online.")])
    db = _mock_db()
    with patch("app.services.query_service.build_agent", return_value=agent):
        result = await run("Latest news?", True, uuid.uuid4(), db)
    assert result["used_web_search"] is True


async def test_run_used_web_search_false_when_not_called() -> None:
    source = _make_source()
    agent = _make_agent([_retrieve_event([source]), _final_state_event("Answer.")])
    db = _mock_db()
    with patch("app.services.query_service.build_agent", return_value=agent):
        result = await run("What is RAG?", False, uuid.uuid4(), db)
    assert result["used_web_search"] is False


async def test_run_persists_query_history() -> None:
    agent = _make_agent([_final_state_event("The answer.")])
    db = _mock_db()
    with patch("app.services.query_service.build_agent", return_value=agent):
        await run("question", False, uuid.uuid4(), db)
    db.add.assert_called_once()
    db.commit.assert_awaited_once()
