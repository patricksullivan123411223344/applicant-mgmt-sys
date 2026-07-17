from pathlib import Path
from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: str = "local"
    database_url: SecretStr = SecretStr("sqlite:///./data/housing_processor.db")
    supabase_url: str | None = None
    supabase_anon_key: SecretStr | None = None
    supabase_service_role_key: SecretStr | None = None
    supabase_jwt_secret: SecretStr | None = None
    # Only honored when ENVIRONMENT=local and DATABASE_URL is SQLite.
    auth_disabled: bool = False
    storage_backend: str = "local"
    storage_root: Path | None = Path("./data/storage")
    llm_enabled: bool = False
    llm_provider: str | None = None
    llm_model: str | None = None
    automatic_match_threshold: int = 100
    review_match_threshold: int = 60
    max_upload_bytes: int = 10_485_760
    allowed_document_types: tuple[str, ...] = (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
