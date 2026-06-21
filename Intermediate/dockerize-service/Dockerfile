# syntax=docker/dockerfile:1
#
# Minimal, production-lean image for the FastAPI currency service.
# - slim base keeps the image small
# - dependencies installed in their own layer for build-cache reuse
# - runs as a non-root user
# - built-in HEALTHCHECK hits /health using Python (no curl needed in the image)

FROM python:3.12-slim AS runtime

# Build metadata: pass at build time with `--build-arg BUILD_ID=$(git rev-parse --short HEAD)`.
# Surfaced by the /health and /ready probes.
ARG BUILD_ID=dev
ENV BUILD_ID=${BUILD_ID}

# Faster, quieter, no .pyc files, unbuffered logs.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

# NOTE: the build context is the monorepo's `Intermediate/` directory (not this
# service folder) so the shared `currency-core` package can be COPYed in. See the
# README "Architecture" section and the CI workflow (`context: Intermediate`).

# 1) Third-party deps first — this layer is cached unless requirements.txt changes.
COPY dockerize-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2) Shared conversion core. Installed non-editable with --no-deps: its runtime
#    deps (fastapi/pydantic) are already satisfied by step 1, so this layer is
#    cheap and only rebuilds when the shared package changes.
COPY shared/currency-core /opt/currency-core
RUN pip install --no-cache-dir --no-deps /opt/currency-core

# 3) Application code (thin entry point).
COPY dockerize-service/app ./app

# 3) Run as a non-root user.
RUN useradd --create-home --uid 10001 appuser
USER appuser

EXPOSE 8000

# Container-native health check against the app's /health endpoint.
HEALTHCHECK --interval=15s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import os,urllib.request,sys; \
url=f'http://127.0.0.1:{os.environ.get(\"PORT\",\"8000\")}/health'; \
sys.exit(0 if urllib.request.urlopen(url, timeout=2).status==200 else 1)" || exit 1

# Start the service via a signal-safe exec-form entrypoint. The Python process
# reads $PORT and execs uvicorn in place, so uvicorn is PID 1 and handles SIGTERM
# directly (graceful shutdown). No `sh -c` wrapper to swallow signals.
CMD ["python", "-m", "app.entrypoint"]
