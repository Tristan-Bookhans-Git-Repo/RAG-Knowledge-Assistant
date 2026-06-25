import uuid

from langchain_core.tools import BaseTool, tool
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.embeddings import get_embeddings
from app.services.vector_store import SimilarityResult, similarity_search


def make_retrieve_tool(user_id: uuid.UUID, db: AsyncSession) -> BaseTool:
    @tool
    async def retrieve(query: str) -> list[SimilarityResult]:
        """Search the user's documents for passages relevant to the query."""
        embedding = get_embeddings().embed_query(query)
        return await similarity_search(db, embedding, user_id)

    return retrieve
