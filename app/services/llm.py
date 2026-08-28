from langchain_core.language_models import BaseChatModel
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from pydantic import SecretStr

from app.config import settings


def get_chat_model() -> BaseChatModel:
    if settings.LLM_PROVIDER == "openai":
        return ChatOpenAI(
            api_key=SecretStr(settings.OPENAI_API_KEY),
            model="gpt-5.6-luna",
        )
    return ChatOllama(base_url=settings.OLLAMA_HOST, model=settings.OLLAMA_CHAT_MODEL)
