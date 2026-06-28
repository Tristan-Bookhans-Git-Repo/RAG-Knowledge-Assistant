import uuid
from typing import Any
from unittest.mock import MagicMock, patch

from app.services.agent import build_agent
from app.services.clarify_tool import clarify_tool


def _build(max_iterations: int = 10, use_web_search: bool = True) -> Any:
    with (
        patch("app.services.agent.get_chat_model") as mock_llm,
        patch("app.services.agent.make_retrieve_tool", return_value=clarify_tool),
    ):
        mock_llm.return_value.bind_tools = MagicMock(return_value=mock_llm.return_value)
        return build_agent(
            uuid.uuid4(),
            MagicMock(),
            max_iterations=max_iterations,
            use_web_search=use_web_search,
        )


def test_build_agent_returns_compiled_graph() -> None:
    agent = _build()
    assert agent is not None


def test_build_agent_graph_has_tools_node() -> None:
    agent = _build()
    assert "tools" in agent.nodes


def test_build_agent_includes_web_search_and_clarify_tools() -> None:
    agent = _build()
    tool_names = set(agent.nodes["tools"].bound.tools_by_name.keys())
    assert "web_search_tool" in tool_names
    assert "clarify_tool" in tool_names


def test_build_agent_respects_max_iterations() -> None:
    agent = _build(max_iterations=5)
    assert agent.config.get("recursion_limit") == 5


def test_build_agent_excludes_web_search_when_disabled() -> None:
    agent = _build(use_web_search=False)
    tool_names = set(agent.nodes["tools"].bound.tools_by_name.keys())
    assert "web_search_tool" not in tool_names
    assert "clarify_tool" in tool_names
