from langchain_core.embeddings import Embeddings
from langchain_ollama import OllamaEmbeddings
from langchain_openai import OpenAIEmbeddings
from pydantic import SecretStr

from app.config import settings


def get_embeddings() -> Embeddings:
    if settings.LLM_PROVIDER == "openai":
        return OpenAIEmbeddings(
            api_key=SecretStr(settings.OPENAI_API_KEY),
            model="text-embedding-3-small",
            dimensions=settings.EMBED_DIM,
        )
    return OllamaEmbeddings(base_url=settings.OLLAMA_HOST, model=settings.OLLAMA_EMBED_MODEL)


def validate_embedding_dim(model: Embeddings) -> None:
    dim = len(model.embed_query("test"))
    expected = settings.EMBED_DIM
    assert dim == expected, f"Embedding dim mismatch: expected {expected}, got {dim}"
