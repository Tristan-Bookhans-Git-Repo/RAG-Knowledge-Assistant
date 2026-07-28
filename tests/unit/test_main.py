from unittest.mock import AsyncMock, patch

from app.main import lifespan


async def test_lifespan_validates_embeddings_and_disposes_engine() -> None:
    with (
        patch("app.main.get_embeddings") as mock_get_embeddings,
        patch("app.main.validate_embedding_dim") as mock_validate,
        patch("app.main.engine") as mock_engine,
    ):
        mock_engine.dispose = AsyncMock()

        async with lifespan(object()):  # type: ignore[arg-type]
            pass

        mock_validate.assert_called_once_with(mock_get_embeddings.return_value)
        mock_engine.dispose.assert_awaited_once()
