import uuid
from typing import Any

from langchain.agents import create_agent
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.clarify_tool import clarify_tool
from app.services.llm import get_chat_model
from app.services.retrieve_tool import make_retrieve_tool
from app.services.web_search_tool import web_search_tool

_SYSTEM_PROMPT = (
    "You are a knowledgeable assistant. "
    "Always use the retrieve tool to search the user's documents before answering. "
    "Ground your answers in the retrieved content and cite your sources. "
    "If the question is unclear or ambiguous, use the clarify tool to ask for more detail. "
    "Only use the web_search_tool if the answer cannot be found in the user's documents."
)

_DEFAULT_MAX_ITERATIONS = 10


def build_agent(
    user_id: uuid.UUID,
    db: AsyncSession,
    max_iterations: int = _DEFAULT_MAX_ITERATIONS,
) -> Any:
    tools = [make_retrieve_tool(user_id, db), web_search_tool, clarify_tool]
    agent = create_agent(
        model=get_chat_model(),
        tools=tools,
        system_prompt=_SYSTEM_PROMPT,
    )
    return agent.with_config({"recursion_limit": max_iterations})
