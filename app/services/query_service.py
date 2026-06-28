import uuid
from typing import Any, TypedDict

from langchain_core.messages import HumanMessage
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.query_history import QueryHistory
from app.services.agent import build_agent
from app.services.vector_store import SimilarityResult


class QueryResult(TypedDict):
    answer: str
    sources: list[SimilarityResult]
    used_web_search: bool


async def run(
    question: str,
    use_web_search: bool,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> QueryResult:
    agent = build_agent(user_id, db, use_web_search=use_web_search)
    sources: list[SimilarityResult] = []
    used_web_search_detected = False
    final_state: dict[str, Any] | None = None

    async for event in agent.astream_events(
        {"messages": [HumanMessage(content=question)]},
        version="v2",
    ):
        kind = event["event"]

        if kind == "on_tool_end":
            tool_name = event.get("name", "")
            if tool_name == "retrieve":
                output = event["data"].get("output")
                if isinstance(output, list):
                    sources.extend(output)
            elif tool_name == "web_search_tool":
                used_web_search_detected = True

        elif kind == "on_chain_end":
            output = event["data"].get("output")
            if isinstance(output, dict) and "messages" in output:
                final_state = output

    answer = ""
    if final_state:
        last_msg = final_state["messages"][-1]
        content = getattr(last_msg, "content", "")
        answer = content if isinstance(content, str) else str(content)

    record = QueryHistory(
        user_id=user_id,
        question=question,
        answer=answer,
        used_web_search=used_web_search_detected,
    )
    db.add(record)
    await db.commit()

    return QueryResult(
        answer=answer,
        sources=sources,
        used_web_search=used_web_search_detected,
    )
