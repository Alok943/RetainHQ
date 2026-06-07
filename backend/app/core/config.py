from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "RetainHQ Backend"
    
    # Supabase Configuration
    SUPABASE_URL: str
    SUPABASE_JWT_SECRET: str
    DATABASE_URL: str

    # Founder/admin gate (email-based; full admin auth deferred). Overridable via env.
    ADMIN_EMAIL: str = "aloksingh98541@gmail.com"

    # Groq LLM recall grader (EXPERIMENT — frozen, off the launch path)
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.1-8b-instant"
    GRADER_ENABLED: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
