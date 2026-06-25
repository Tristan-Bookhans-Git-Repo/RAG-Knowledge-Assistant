from typing import Any, cast

from langchain_core.tools import tool

from app.config import settings


@tool
def web_search_tool(query: str) -> list[dict[str, Any]] | dict[str, str]:
    """Search the web for information relevant to the query."""
    if not settings.TAVILY_API_KEY:
        return {"status": "disabled"}
    from langchain_tavily import TavilySearch

    results = TavilySearch(max_results=5).invoke({"query": query})
    return cast(list[dict[str, Any]], results)
