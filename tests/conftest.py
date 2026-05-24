import os

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://raguser:ragpass@db:5432/ragdb")
os.environ.setdefault("JWT_SECRET", "test-secret-do-not-use-in-production")
