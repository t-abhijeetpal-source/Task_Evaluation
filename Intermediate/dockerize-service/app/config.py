"""Application configuration via environment variables (pydantic-settings).

All knobs are environment-driven so the same image runs unchanged across envs.
CORS fails *closed* in production: if ``ENV=production`` and ``CORS_ORIGINS`` is
unset, no origin is allowed (rather than silently permitting localhost).

NOTE: authentication/authorization is intentionally OUT OF SCOPE here — see the
README. Add API-key/JWT/mTLS at the edge or as additional middleware for prod.
"""

from typing import List, Optional

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_DEV_CORS_ORIGINS = ["http://localhost:3000", "http://localhost:8000"]


class Settings(BaseSettings):
    """Runtime settings. Field names map to UPPER_SNAKE env vars."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Deployment environment: "development" | "production" | ...
    env: str = "development"

    # Allowed CORS origins. Provide as a comma-separated env value, e.g.
    #   CORS_ORIGINS="https://app.example.com,https://admin.example.com"
    # Left unset -> dev defaults (localhost) in development, deny-all in production.
    cors_origins: Optional[List[str]] = None

    # Per-IP request budget for /convert (fixed 60s window).
    rate_limit_per_minute: int = 60

    # Maximum accepted request body size, in bytes (1 KiB default).
    max_body_bytes: int = 1024

    # Build/version metadata surfaced by the health/readiness probes.
    build_id: str = "dev"
    service_version: str = "1.0.0"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_csv(cls, v):
        """Accept a comma-separated string in addition to a JSON list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @property
    def is_production(self) -> bool:
        return self.env.strip().lower() == "production"

    @property
    def resolved_cors_origins(self) -> List[str]:
        """Effective allow-list: explicit value wins; else env-appropriate default."""
        if self.cors_origins is not None:
            return self.cors_origins
        return [] if self.is_production else list(_DEV_CORS_ORIGINS)
