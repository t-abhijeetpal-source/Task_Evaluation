# syntax=docker/dockerfile:1
#
# Minimal, production-lean image for the FastAPI currency service.
# - slim base keeps the image small
# - dependencies installed in their own layer for build-cache reuse
# - runs as a non-root user
# - built-in HEALTHCHECK hits /health using Python (no curl needed in the image)

FROM python:3.12-slim AS runtime

# Faster, quieter, no .pyc files, unbuffered logs.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

WORKDIR /app

# 1) Dependencies first — this layer is cached unless requirements.txt changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2) Application code.
COPY app ./app

# 3) Run as a non-root user.
RUN useradd --create-home --uid 10001 appuser
USER appuser

EXPOSE 8000

# Container-native health check against the app's /health endpoint.
HEALTHCHECK --interval=15s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import os,urllib.request,sys; \
url=f'http://127.0.0.1:{os.environ.get(\"PORT\",\"8000\")}/health'; \
sys.exit(0 if urllib.request.urlopen(url, timeout=2).status==200 else 1)" || exit 1

# Start the service. Uses $PORT so the port is configurable at run time.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
