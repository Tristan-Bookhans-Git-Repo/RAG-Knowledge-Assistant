from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://raguser:ragpass@db:5432/ragdb"
    LLM_PROVIDER: str = "ollama"
    OLLAMA_HOST: str = "http://ollama:11434"
    OLLAMA_CHAT_MODEL: str = "qwen2.5:7b"
    OLLAMA_EMBED_MODEL: str = "nomic-embed-text"
    OPENAI_API_KEY: str = ""
    EMBED_DIM: int = 768
    JWT_SECRET: str = "supersecretkey"
    JWT_ACCESS_TTL_MINUTES: int = 15
    JWT_REFRESH_TTL_DAYS: int = 7
    SECURE_COOKIES: bool = False
    TAVILY_API_KEY: str = ""

    model_config = {"env_file": ".env"}


settings = Settings()
