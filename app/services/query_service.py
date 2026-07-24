import uuid
from typing import Any, Literal, TypedDict

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.query_history import QueryHistory
from app.services.agent import build_agent
from app.services.vector_store import SimilarityResult


class QueryResult(TypedDict):
    type: Literal["answer", "clarification"]
    answer: str
    sources: list[SimilarityResult]
    used_web_search: bool


async def run(
    question: str,
    use_web_search: bool,
    user_id: uuid.UUID,
    db: AsyncSession,
    llm: BaseChatModel | None = None,
) -> QueryResult:
    agent = build_agent(user_id, db, use_web_search=use_web_search, llm=llm)
    sources: list[SimilarityResult] = []
    used_web_search_detected = False
    response_type: Literal["answer", "clarification"] = "answer"
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
                # ToolNode wraps every tool return in a ToolMessage and stringifies
                # non-str content — the raw list survives on .artifact instead
                # (see retrieve_tool.py's response_format="content_and_artifact")
                artifact = getattr(output, "artifact", None)
                if isinstance(artifact, list):
                    sources.extend(artifact)
            elif tool_name == "web_search_tool":
                used_web_search_detected = True
            elif tool_name == "clarify_tool":
                response_type = "clarification"

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
        type=response_type,
        answer=answer,
        sources=sources,
        used_web_search=used_web_search_detected,
    )
