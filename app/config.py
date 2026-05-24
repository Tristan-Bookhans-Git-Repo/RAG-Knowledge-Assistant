from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    LLM_PROVIDER: str = "ollama"
    OLLAMA_HOST: str = "http://ollama:11434"
    OLLAMA_CHAT_MODEL: str = "llama3.2"
    OLLAMA_EMBED_MODEL: str = "nomic-embed-text"
    OPENAI_API_KEY: str = ""

    model_config = {"env_file": ".env"}


settings = Settings()
