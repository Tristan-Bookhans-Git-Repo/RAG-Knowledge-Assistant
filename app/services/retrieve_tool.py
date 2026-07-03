import uuid

from langchain_core.tools import BaseTool, tool
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.embeddings import get_embeddings
from app.services.vector_store import SimilarityResult, similarity_search


def make_retrieve_tool(user_id: uuid.UUID, db: AsyncSession) -> BaseTool:
    @tool(response_format="content_and_artifact")
    async def retrieve(query: str) -> tuple[str, list[SimilarityResult]]:
        """Search the user's documents for passages relevant to the query."""
        embedding = get_embeddings().embed_query(query)
        results = await similarity_search(db, embedding, user_id)
        # content: a plain-text summary for the LLM to reason over
        # artifact: the raw results, preserved for the caller (see query_service.run,
        # which reads ToolMessage.artifact instead of the stringified .content —
        # ToolNode always stringifies non-str returns into .content, which would
        # otherwise turn UUIDs into unparseable repr() text)
        content = "\n\n".join(r["content"] for r in results) or "No relevant passages found."
        return content, results

    return retrieve
