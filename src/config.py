from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "URL Shortener Service"
    base_url: str = "http://localhost:8000"
    database_url: str = "postgresql+psycopg://postgres:postgres@db:5432/url_shortener"
    redis_url: str = "redis://redis:6379/0"
    cache_ttl_seconds: int = 3600

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
