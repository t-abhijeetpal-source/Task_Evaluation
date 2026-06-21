# I5 — Dockerized Currency Conversion Service

A FastAPI currency-conversion service, containerized and production-hardened. Endpoints:
`POST /convert`, `GET /health` (liveness), `GET /ready` (readiness), `GET /metrics` (Prometheus).

Hardening highlights: exact-`Decimal` money with non-finite rejection, CORS + security
headers + per-IP rate limiting + body-size cap, structured JSON logs with request
correlation IDs, Prometheus metrics, K8s-style probes, and a signal-safe entrypoint.

> **Verification status:** ✅ Built, run, and verified in Docker (Colima). Image
> `currency-service:1.0` (55 MB content) builds; container runs **Up (healthy)**; `/health`→ok,
> `/convert`→8300, unsupported→400. Full evidence in `VERIFICATION_RESULTS.md`.
> (On this corporate network the Colima VM needed the corporate root CA trusted to pull the base
> image — documented in VERIFICATION_RESULTS.md.)

---

## Architecture — shared `currency-core` package

This service does **not** carry its own copy of the conversion logic. The schemas,
service logic, and the `POST /convert` route live once in the
[`currency-core`](../shared/currency-core) package (`Intermediate/shared/currency-core`),
imported by both this service (I5) and the I4 polyglot service. This service's `app/`
holds only its production concerns — `main.py` (app assembly), config, middleware,
metrics, probes, error handling, and entrypoint — and mounts `currency_core.routes.router`.
Probes/metrics are service-specific and intentionally not shared.

- **Dev / tests:** `requirements-dev.txt` installs the package editable
  (`-e ../shared/currency-core`).
- **Docker:** the image copies `shared/currency-core` and installs it non-editable
  (`pip install --no-deps`), after the third-party deps layer — so layer caching is
  preserved and the runtime is self-contained (image stays independently deployable).

**Why a shared package (Option A)** over the alternatives — (B) having I5 `COPY` I4's
`app/` directly (couples the build to a sibling path, no version boundary) or (C) a git
submodule (heavyweight for a single repo): Option A is DRY, versioned in `pyproject.toml`,
and independently testable, while each service keeps its own image/run lifecycle.

## Prerequisites

A working Docker engine. On macOS via Colima (already installed here):

```bash
colima start            # starts the Linux VM that backs Docker
docker info             # should print engine details
```

## Build

The build context is the monorepo's `Intermediate/` directory (not this folder), so the
shared `currency-core` package can be copied into the image. A whitelist `.dockerignore`
at `Intermediate/.dockerignore` keeps the context small (only `shared/` + this service).

```bash
cd Intermediate
docker build -f dockerize-service/Dockerfile -t currency-service:1.0 .
```

## Run

```bash
docker run -d --name currency -p 8000:8000 currency-service:1.0
docker ps                       # container should be "Up (healthy)" after ~5s
```

## Verification

```bash
# liveness
curl localhost:8000/health
# -> {"status":"ok","version":"1.0.0","build":"dev"}

# readiness
curl localhost:8000/ready
# -> {"status":"ok","version":"1.0.0","build":"dev"}   (503 if rates/config missing)

# conversion
curl -X POST localhost:8000/convert -H 'Content-Type: application/json' \
  -d '{"amount":100,"from":"USD","to":"INR"}'
# -> {"converted_amount":8300,"from":"USD","to":"INR"}

# non-finite amount rejected at the boundary (422)
curl -X POST localhost:8000/convert -H 'Content-Type: application/json' \
  -d '{"amount":1e308,"from":"USD","to":"INR"}'
# -> 422 {"detail":[...]}

# Prometheus metrics
curl localhost:8000/metrics | head
# -> http_requests_total{...} ...

# container's own health check
docker inspect --format '{{.State.Health.Status}}' currency
# -> healthy
```

## Stop

```bash
docker stop currency
docker rm currency              # remove the container
docker rmi currency-service:1.0 # remove the image (optional)
```

## CI

Every push or pull request that touches `Intermediate/dockerize-service/**` triggers the
[`i5-dockerize-service`](../../.github/workflows/dockerize-service.yml) job
(`.github/workflows/dockerize-service.yml`). The job is **path-filtered**, uses a
`concurrency` group to cancel superseded runs, and runs on Python 3.12:

1. **Lint** — `ruff check .`
2. **Test** — `pytest -v` (test results uploaded as an artifact on failure)
3. **Build** — `docker build` via buildx with GitHub Actions layer cache, tagged
   `currency-service:ci-<sha>` (`push: false`)
4. **Smoke test** — runs the image (with `BUILD_ID=<git-sha>`), waits for the container
   `HEALTHCHECK` to report `healthy`, then asserts `/health` and `/ready` report
   `"status":"ok"` and `/convert` returns `8300`

The pipeline fails on any lint, test, build, or smoke-test failure and is sized to finish
in under 5 minutes.

> **Future step — registry push:** the build currently uses `push: false`. To publish,
> add `docker/login-action` (to GHCR) and flip `push: true` with semver tags
> (e.g. `ghcr.io/<owner>/currency-service:<version>`). Production hardening to follow:
> Trivy image scan, SBOM generation, and signed images.

## Run tests

The service ships with a pytest suite (31 tests) exercising conversion, validation,
security, observability, and probes via FastAPI's `TestClient` — no live server or
Docker engine required.

```bash
cd Intermediate/dockerize-service
python3 -m venv .venv && . .venv/bin/activate          # optional but recommended
pip install -r requirements.txt -r requirements-dev.txt
pytest -v                                              # run the suite
pytest --co -q                                         # list collected tests
```

Coverage by file:

| File | What it covers |
|---|---|
| `test_convert.py` | happy path, same-currency, unsupported (400), non-positive (422), malformed (422), Decimal inf/NaN/huge rejection, precision |
| `test_security.py` | security headers, CORS allow/deny + prod fail-closed, 429 rate limit, 413 body cap |
| `test_observability.py` | `/metrics` Prometheus output, `X-Request-ID` generation + propagation |
| `test_health.py` | `/health` liveness (version/build), `/ready` 200 + 503-when-not-ready |
| `test_entrypoint.py` | signal-safe entrypoint argv (default + custom `PORT`) |

## Configuration

All configuration is environment-driven (see `app/config.py`, `pydantic-settings`).
Copy [`.env.example`](.env.example) to `.env` for local dev, or pass `-e` flags to `docker run`.

| Env var | Default | Purpose |
|---|---|---|
| `PORT` | `8000` | Port uvicorn binds inside the container |
| `ENV` | `development` | `production` makes CORS fail closed (deny all unless `CORS_ORIGINS` set) |
| `CORS_ORIGINS` | dev: localhost / prod: deny | Comma-separated allow-list, e.g. `https://a.com,https://b.com` |
| `RATE_LIMIT_PER_MINUTE` | `60` | Per-IP request budget for `/convert` (60s window) |
| `MAX_BODY_BYTES` | `1024` | Max accepted request body size (bytes); larger → `413` |
| `BUILD_ID` | `dev` | Build identifier reported by `/health` and `/ready` (wire to git SHA) |
| `LOG_LEVEL` | `INFO` | Log level for the JSON logger |

```bash
docker run -d --name currency -e PORT=9000 -p 9000:9000 currency-service:1.0
```

## Validation & precision (financial domain)

Amounts use **`Decimal`**, never `float`, so arithmetic is exact and bad input is rejected
at the API boundary:

| Input | Result |
|---|---|
| `Infinity` / `NaN` (number **or** string) | `422` — rejected by the schema (`finite_number`) |
| magnitude beyond 20 significant digits (e.g. `1e308`) | `422` — exceeds `max_digits` |
| precision beyond 6 decimal places | `422` — exceeds `decimal_places` |
| `<= 0` | `422` `{"error":"Amount must be positive"}` (business rule, service layer) |

Precision policy: at most **6 decimal places**, **20 significant digits**; results are rounded
`HALF_UP` and rendered as an integer when integral (`8300`) or a trimmed decimal otherwise
(`9.2`). A custom 422 handler sanitises non-finite inputs so malformed requests never 500.

## API security

Middleware order (outermost → innermost): **security headers → CORS → request-context
→ rate limit → body-size cap → routes**.

- **Security headers** on every response: `X-Content-Type-Options: nosniff`,
  `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`,
  `Content-Security-Policy: default-src 'none'; frame-ancestors 'none'`.
- **CORS** from `CORS_ORIGINS`; fails **closed** in `ENV=production`.
- **Rate limiting**: per-IP fixed-window on `/convert` (`429 {"error":"Rate limit exceeded"}`
  with `Retry-After`). `/health`, `/ready`, `/metrics` are exempt. In-memory (single replica);
  use a shared store (Redis) for multi-replica.
- **Body-size cap**: requests over `MAX_BODY_BYTES` get `413`.

> **Auth is out of scope.** Add API-key / JWT / mTLS (middleware or edge) and a WAF for production.

## Observability

- **Structured JSON logs** to stdout (one object per request; bodies never logged):

  ```json
  {"timestamp":"2026-06-21T07:58:51.820291+00:00","level":"INFO","logger":"currency-service",
   "message":"request_completed","request_id":"demo-123","method":"POST","path":"/convert",
   "status_code":200,"duration_ms":2.34,"client":"127.0.0.1"}
  ```

- **Correlation IDs**: every response carries `X-Request-ID` (a client-supplied one is
  propagated; otherwise generated).
- **Prometheus** at `GET /metrics`: `http_requests_total`, `http_request_errors_total`,
  `http_request_duration_seconds` (labelled by method + matched route). Scrape config:

  ```yaml
  scrape_configs:
    - job_name: currency-service
      metrics_path: /metrics
      static_configs:
        - targets: ["currency-service:8000"]
  ```

## Probes (Kubernetes)

| Probe | Path | Semantics | Failure |
|---|---|---|---|
| Liveness | `GET /health` | process up / event loop responsive | restart pod |
| Readiness | `GET /ready` | config loaded **and** rates table non-empty | stop routing traffic (`503`) |

Both return `{"status":"ok","version":"<v>","build":"<BUILD_ID>"}`. The Docker `HEALTHCHECK`
hits `/health` (unchanged), so it stays backward compatible with existing scripts.

## Signal-safe entrypoint

The container starts via `CMD ["python","-m","app.entrypoint"]`. The entrypoint reads `$PORT`
and `os.execvp`s uvicorn **in place**, so uvicorn becomes PID 1 and receives `SIGTERM` from
`docker stop` directly — graceful shutdown within the stop grace period. No `sh -c` wrapper
swallows signals. `PORT` remains overridable (`-e PORT=9000`) and the `HEALTHCHECK` honours it.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `Cannot connect to the Docker daemon` | engine not running | `colima start` (macOS) / start Docker Desktop |
| `no space left on device` during build/VM start | disk full | free several GB, then `colima start` |
| container exits immediately | bad start command / import error | `docker logs currency` |
| `curl: connection refused` | port not published / app still starting | check `-p 8000:8000`; wait for `healthy` |
| health shows `unhealthy` | `/health` not responding | `docker logs currency`; verify `PORT` matches `-p` |
