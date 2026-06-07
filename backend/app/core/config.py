from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "RetainHQ Backend"
    DEBUG: bool = False

    # Supabase Configuration
    SUPABASE_URL: str
    SUPABASE_JWT_SECRET: str
    DATABASE_URL: str

    # CORS — comma-separated origins from env. Localhost included for dev convenience.
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    # Founder/admin gate — must be set via env (no hardcoded default).
    ADMIN_EMAIL: str

    # DB pool tuning (match to your deploy worker count)
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30

    # Groq LLM recall grader (EXPERIMENT — frozen, off the launch path)
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.1-8b-instant"
    GRADER_ENABLED: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
