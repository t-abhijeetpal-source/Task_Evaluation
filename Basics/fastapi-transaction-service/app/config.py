"""Application configuration — 12-factor, environment-driven.

Centralises every tunable so nothing is hardcoded in the app body. Values are
read once at import time from the process environment, with safe defaults for
local dev. Swap these via real env vars / a secrets manager in production.
"""

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    """Immutable runtime settings, sourced from the environment."""

    app_name: str = os.environ.get("APP_NAME", "Transaction Tracking Service")
    app_version: str = os.environ.get("APP_VERSION", "1.1.0")
    log_level: str = os.environ.get("LOG_LEVEL", "INFO").upper()
    # Reject implausibly large amounts (defence against overflow / fat-finger).
    max_amount: float = float(os.environ.get("MAX_AMOUNT", "1000000000"))  # 1e9


settings = Settings()
