# Digest-pinned base for reproducible, supply-chain-verifiable builds.
# python:3.12-slim (3.12.13) — repin with: docker inspect --format='{{index .RepoDigests 0}}' python:3.12-slim
FROM python:3.12-slim@sha256:d764629ce0ddd8c71fd371e9901efb324a95789d2315a47db7e4d27e78f1b0e9

ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY worker.py .

# Run as a non-root user (defense in depth; UID matches the D4 K8s
# securityContext runAsUser 10001 so images are interchangeable across stacks).
RUN useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin appuser
USER 10001

# The worker installs a SIGTERM handler for graceful drain; `docker stop` sends
# SIGTERM, so it finishes its current batch and exits 0 instead of being killed.
CMD ["python", "worker.py"]
