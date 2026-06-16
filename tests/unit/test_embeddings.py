import pytest
from langchain_ollama import OllamaEmbeddings
from langchain_openai import OpenAIEmbeddings

from app.config import settings
from app.services.embeddings import get_embeddings, validate_embedding_dim

# ---------------------------------------------------------------------------
# Provider selection
# ---------------------------------------------------------------------------


def test_ollama_provider_returns_ollama_embeddings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "LLM_PROVIDER", "ollama")
    assert isinstance(get_embeddings(), OllamaEmbeddings)


def test_ollama_provider_uses_configured_model(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "LLM_PROVIDER", "ollama")
    model = get_embeddings()
    assert model.model == settings.OLLAMA_EMBED_MODEL


def test_openai_provider_returns_openai_embeddings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "LLM_PROVIDER", "openai")
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "sk-test")
    assert isinstance(get_embeddings(), OpenAIEmbeddings)


def test_openai_provider_passes_configured_dimensions(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "LLM_PROVIDER", "openai")
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "sk-test")
    model = get_embeddings()
    assert model.dimensions == settings.EMBED_DIM


# ---------------------------------------------------------------------------
# Dimension validation
# ---------------------------------------------------------------------------


class _FakeModel:
    def __init__(self, dim: int) -> None:
        self._dim = dim

    def embed_query(self, text: str) -> list[float]:
        return [0.0] * self._dim


def test_validate_embedding_dim_passes_for_correct_dimension() -> None:
    validate_embedding_dim(_FakeModel(settings.EMBED_DIM))


def test_validate_embedding_dim_raises_for_wrong_dimension() -> None:
    with pytest.raises(AssertionError):
        validate_embedding_dim(_FakeModel(settings.EMBED_DIM + 1))
