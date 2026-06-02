from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "RetainHQ Backend"
    
    # Supabase Configuration
    SUPABASE_URL: str
    SUPABASE_JWT_SECRET: str
    DATABASE_URL: str

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
