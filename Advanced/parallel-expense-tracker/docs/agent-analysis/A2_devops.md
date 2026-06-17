# A2 DevOps Analysis

## Docker Strategy

- **Base image:** `python:3.12-slim` for a small, predictable runtime.
- **Layer caching:** `requirements.txt` is copied and installed (`pip install --no-cache-dir -r requirements.txt`) *before* application code is copied, so dependency installation is cached and only re-runs when requirements change.
- **Application copy:** `app/` and `static/` are copied separately so app-code changes don't bust the dependency layer.
- **Data directory:** `/app/data` is created at build time so the SQLite file (`data/expenses.db`) has a home; it is provided at runtime via a bind mount (see Compose).
- **Non-root runtime:** a dedicated `appuser` (uid 1000) is created and owns `/app`; the container runs as `appuser`, not root.
- **Environment:** `PYTHONDONTWRITEBYTECODE=1` and `PYTHONUNBUFFERED=1` to avoid `.pyc` clutter and to stream logs immediately.
- **Port:** `EXPOSE 8000`.
- **.dockerignore** excludes `.venv`, `__pycache__`, `*.pyc`, `.pytest_cache`, `tests/`, `data/`, `docs/`, `.git`, `*.md`, and `.github` to keep the build context minimal and reproducible (the DB and tests never enter the image).

## Compose Layout

- Single service `app` building the local `Dockerfile` (image tag `expense-tracker:local`).
- Port mapping `8000:8000`.
- Bind volume `./data:/app/data` so the SQLite database persists across container restarts/rebuilds.
- `restart: unless-stopped` for resilience.
- Healthcheck mirrors the Dockerfile `HEALTHCHECK` (stdlib urllib against `/api/health`).

## CI Stages (`.github/workflows/ci.yml`)

Triggers on `push` and `pull_request`.

1. **`test`** — Ubuntu runner, `actions/setup-python@v5` (Python 3.12), `pip install -r requirements.txt`, then `pytest -v`.
2. **`build`** (`needs: test`) — Checks out the repo and runs `docker build -t expense-tracker:ci .`. Runs only after tests pass.

## Health Check Approach

The image is `slim` and has no `curl`. The health check uses the Python standard library instead:

```
python -c "import urllib.request,sys; sys.exit(0) if urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=4).status == 200 else sys.exit(1)"
```

Configured with `--interval=30s --timeout=5s --start-period=10s --retries=3` in the Dockerfile, and mirrored in `docker-compose.yml`. The endpoint `/api/health` is served by the FastAPI router (`app/routes.py`, prefix `/api`).

## Exact Build / Run Commands

```bash
# Build the image
docker build -t expense-tracker:ci .

# Run directly with Docker (persist the DB via a host bind mount)
docker run -d --name expense-tracker -p 8000:8000 -v "$(pwd)/data:/app/data" expense-tracker:ci

# Or via Compose
docker compose up --build -d

# Check health / tear down
docker ps                       # STATUS column shows (healthy)
docker compose down

# App entrypoint inside the container
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Agent Generated

These DevOps artifacts (Dockerfile, .dockerignore, docker-compose.yml, .github/workflows/ci.yml) were authored by the DevOps agent. The Docker build, container run, Compose up, and CI workflow have **NOT YET BEEN RUN** — the coordinator verifies build/run in Phase 4.
