from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "JobCodex"
    debug: bool = False
    personal_user_email: str = "personal@jobcodex.local"
    portfolio_path: str = "portfolio.md"
    job_scan_interval_hours: int = 24
    
    database_url: str = "sqlite+aiosqlite:///./jobcodex.db"
    
    secret_key: str = "dev-secret-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]
    
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    ai_temperature: float = 0.7
    ai_max_tokens: int = 500
    
    job_fetch_interval_hours: int = 6
    max_jobs_per_fetch: int = 100

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()
