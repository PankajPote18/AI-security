"""Application settings, loaded from the process environment and `.env` (repo root). No secret
ever has a real default here - only `.env.example`-documented placeholders would be wrong to
ship, so required secrets have no default at all and fail fast on startup instead.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

_REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_REPO_ROOT / ".env"), env_file_encoding="utf-8", extra="ignore"
    )

    database_url: str
    test_database_url: str = ""

    jwt_secret_key: SecretStr
    jwt_algorithm: str = "HS256"
    jwt_access_ttl_minutes: int = 60

    cors_allowed_origins: str = "http://localhost:5173"

    ml_model_dir: Path = _REPO_ROOT / "ml" / "models"
    knowledge_base_dir: Path = _REPO_ROOT / "knowledge-base"

    rate_limit_analyze: str = "20/minute"

    # LLM (Stage 3): optional. Report generation degrades to report=null when unset, rather than
    # the app failing to start - see llm/client.py.
    hf_token: SecretStr | None = None
    hf_model: str = "openai/gpt-oss-20b"

    # Threat intelligence (Stage 4): optional. Degrades to status="unavailable" when unset - see
    # security_analysis_service.py.
    urlhaus_auth_key: SecretStr | None = None

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]  # fields are populated from env/.env at runtime
