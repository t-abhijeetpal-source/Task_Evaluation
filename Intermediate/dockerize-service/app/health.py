"""Kubernetes-style probes.

* liveness  — "is the process up / event loop running?" Always ok if we can
              answer the request. Backs the Docker HEALTHCHECK (path ``/health``).
* readiness — "is the service ready to serve traffic?" Verifies configuration is
              loaded and the rates table is non-empty; returns 503 otherwise so
              an orchestrator stops routing traffic to a misconfigured replica.

Both responses include ``version`` and ``build`` metadata (build wired from the
``BUILD_ID`` Docker build arg / env).
"""

from typing import Dict, Tuple

from app.config import Settings
from currency_core import services


def _meta(settings: Settings) -> Dict[str, str]:
    return {"version": settings.service_version, "build": settings.build_id}


def liveness(settings: Settings) -> Dict[str, str]:
    """Liveness: ok as long as we are running."""
    return {"status": "ok", **_meta(settings)}


def readiness(settings: Settings) -> Tuple[Dict[str, str], int]:
    """Readiness: ok only when config is loaded and rates are available.

    Returns ``(body, status_code)`` — 200 when ready, 503 when not.
    """
    is_ready = bool(services.RATES) and bool(services.SUPPORTED_CURRENCIES)
    body = {"status": "ok" if is_ready else "not ready", **_meta(settings)}
    return body, (200 if is_ready else 503)
