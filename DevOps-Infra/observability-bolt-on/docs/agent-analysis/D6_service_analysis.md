# D6 — Phase 1: Service Analysis & Architectural Audit

Every instrumentation decision below matches **file-level evidence**. The "existing
service" instrumented here is the D3/D4 FastAPI service, copied into `D6/` so the
observability bolt-on is self-contained and reproducible.

## Baseline (pre-instrumentation) audit

| Concern | Finding | Evidence |
|---|---|---|
| Runtime | Python 3.12 | `Dockerfile:1` (`FROM python:3.12-slim`) |
| Framework | FastAPI + Uvicorn (ASGI) | `requirements.txt:1-2` |
| Request flow | `uvicorn → FastAPI router → endpoint fn` | `app/main.py` CMD `Dockerfile` |
| Endpoints | `/health`, `/ready`, `/`, `/add` | inherited from D4 `app/main.py` |
| **Logging (before)** | Uvicorn default **plain-text** access lines (`INFO: ... "GET /x" 200`) — unstructured, no request_id/duration | D4 pod logs in `../D4/docs/agent-analysis/D4_kubernetes_validation_record.md` §4 |
| **Metrics (before)** | **None** — no `/metrics`, no client library | D4 `requirements.txt` (no prometheus dep) |
| Monitoring endpoint | only `/health` (liveness), not telemetry | `app/main.py` |

## Instrumentation design (mapped to libraries)

| Phase | Decision | Library / file evidence |
|---|---|---|
| 2 — Structured logs | JSON-line formatter on stdout with `timestamp, level, request_id, method, path, status_code, duration_ms, client, error(stacktrace)` | stdlib `logging` + custom `app/logging_setup.py` (`JsonFormatter`) |
| 3 — Metrics client | `prometheus-client` (the framework-appropriate Python client) | `requirements.txt:4` (`prometheus-client==0.21.1`); `app/metrics.py` |
| 3 — Scrape route | `GET /metrics` via `generate_latest()` | `app/main.py` (`@app.get("/metrics")`) |
| 2+3 — Capture point | one ASGI HTTP middleware times every request, stamps a `request_id`, logs JSON, updates metrics | `app/main.py` (`observability_middleware`) |

## Metric vectors chosen (and why)

- `http_requests_total{method,path,status_code}` — **Counter**, total throughput broken down by outcome.
- `http_request_errors_total{method,path,status_code}` — **Counter**, isolates `status >= 400` for a clean error-rate panel.
- `http_request_duration_seconds{method,path}` — **Histogram** (buckets 5ms…5s) for latency quantiles (`histogram_quantile`).
- Default `process_*` / `python_*` collectors via `ProcessCollector`/`PlatformCollector`.

**Cardinality control:** the `path` label is the matched **route template**
(`request.scope["route"].path`), not the raw URL — so `/add?a=1` and `/add?a=2`
collapse to `path="/add"` (`app/main.py:_route_template`). The `/metrics` path is
excluded from its own counters to avoid scrape self-noise.

## Stack topology

```
generate-load.sh ─HTTP─▶ app:8000 (FastAPI, /metrics)
                              ▲  scrape /metrics every 5s
                              │
                        prometheus:9090 ◀─datasource(proxy)── grafana:3000
                                                              (provisioned dashboard)
```
Evidence: `docker-compose.yml` (3 services), `prometheus/prometheus.yml` (scrape
target `app:8000`), `grafana/provisioning/datasources/datasource.yml` (url
`http://prometheus:9090`), `grafana/provisioning/dashboards/d6-dashboard.json`.
