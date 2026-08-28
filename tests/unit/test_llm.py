import pytest
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

from app.config import settings
from app.services.llm import get_chat_model


def test_ollama_provider_returns_chat_ollama(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "LLM_PROVIDER", "ollama")
    assert isinstance(get_chat_model(), ChatOllama)


def test_ollama_provider_uses_configured_host(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "LLM_PROVIDER", "ollama")
    model = get_chat_model()
    assert isinstance(model, ChatOllama)
    assert model.base_url == settings.OLLAMA_HOST


def test_ollama_provider_uses_configured_chat_model(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "LLM_PROVIDER", "ollama")
    model = get_chat_model()
    assert isinstance(model, ChatOllama)
    assert model.model == settings.OLLAMA_CHAT_MODEL


def test_openai_provider_returns_chat_openai(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "LLM_PROVIDER", "openai")
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "sk-test")
    assert isinstance(get_chat_model(), ChatOpenAI)


def test_openai_provider_defaults_to_gpt56luna(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "LLM_PROVIDER", "openai")
    monkeypatch.setattr(settings, "OPENAI_API_KEY", "sk-test")
    model = get_chat_model()
    assert isinstance(model, ChatOpenAI)
    assert model.model_name == "gpt-5.6-luna"
