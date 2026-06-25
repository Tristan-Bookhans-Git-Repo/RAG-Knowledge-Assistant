import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.retrieve_tool import make_retrieve_tool
from app.services.vector_store import SimilarityResult


def _make_expected(chunk_id: uuid.UUID, doc_id: uuid.UUID) -> list[SimilarityResult]:
    return [
        SimilarityResult(
            id=chunk_id,
            content="relevant passage",
            document_id=doc_id,
            chunk_index=0,
            similarity=0.95,
        )
    ]


async def test_retrieve_tool_calls_similarity_search_with_correct_args() -> None:
    user_id = uuid.uuid4()
    expected = _make_expected(uuid.uuid4(), uuid.uuid4())
    mock_db = MagicMock()
    fake_embedding = [0.1] * 768
    mock_search = AsyncMock(return_value=expected)

    with (
        patch("app.services.retrieve_tool.get_embeddings") as mock_embeddings,
        patch("app.services.retrieve_tool.similarity_search", mock_search),
    ):
        mock_embeddings.return_value.embed_query.return_value = fake_embedding
        retrieve_tool = make_retrieve_tool(user_id, mock_db)
        await retrieve_tool.ainvoke({"query": "what is RAG?"})

    mock_search.assert_called_once_with(mock_db, fake_embedding, user_id)


async def test_retrieve_tool_returns_similarity_results() -> None:
    user_id = uuid.uuid4()
    expected = _make_expected(uuid.uuid4(), uuid.uuid4())
    mock_db = MagicMock()
    mock_search = AsyncMock(return_value=expected)

    with (
        patch("app.services.retrieve_tool.get_embeddings") as mock_embeddings,
        patch("app.services.retrieve_tool.similarity_search", mock_search),
    ):
        mock_embeddings.return_value.embed_query.return_value = [0.0] * 768
        retrieve_tool = make_retrieve_tool(user_id, mock_db)
        result = await retrieve_tool.ainvoke({"query": "what is RAG?"})

    assert result == expected


def test_retrieve_tool_user_id_not_in_schema() -> None:
    user_id = uuid.uuid4()
    mock_db = MagicMock()

    with (
        patch("app.services.retrieve_tool.get_embeddings"),
        patch("app.services.retrieve_tool.similarity_search"),
    ):
        retrieve_tool = make_retrieve_tool(user_id, mock_db)

    assert "user_id" not in retrieve_tool.args
    assert "query" in retrieve_tool.args
