# D6 — Observability Bolt-On (Structured Logs + Metrics + Prometheus/Grafana)

Adds production-grade observability to a small **FastAPI** service: structured **JSON
logging** (request_id, status, duration, stack traces), a Prometheus **`/metrics`**
endpoint (request/error counters + latency histogram), and a self-contained
**app + Prometheus + Grafana** compose stack with **dashboards-as-code**. Proven
end-to-end with a load generator and live dashboard queries.

Evidence: [`docs/agent-analysis/D6_observability_record.md`](docs/agent-analysis/D6_observability_record.md)
· Analysis: [`docs/agent-analysis/D6_service_analysis.md`](docs/agent-analysis/D6_service_analysis.md)

## Telemetry chain

```mermaid
flowchart LR
    LG["generate-load.sh"] -->|HTTP| APP["app:8000<br/>FastAPI + /metrics"]
    PROM["prometheus:9090"] -->|scrape /metrics 5s| APP
    GRAF["grafana:3000<br/>provisioned dashboard"] -->|datasource proxy| PROM
```

## Layout

```
D6/
├── app/
│   ├── main.py            # FastAPI + observability middleware + /metrics route
│   ├── logging_setup.py   # JSON structured logging
│   ├── metrics.py         # prometheus-client counters + histogram
│   └── calc.py
├── tests/                 # pytest (5 tests)
├── Dockerfile             # non-root app image
├── docker-compose.yml     # app + prometheus + grafana
├── prometheus/prometheus.yml
├── grafana/provisioning/
│   ├── datasources/datasource.yml      # Prometheus datasource (as code)
│   └── dashboards/
│       ├── dashboards.yml              # file provider
│       └── d6-dashboard.json           # 4-panel dashboard (as code)
├── scripts/generate-load.sh
└── docs/agent-analysis/
```

## Endpoints

| Path | Purpose |
|---|---|
| `GET /health`, `/ready` | liveness / readiness |
| `GET /` | service info |
| `GET /add?a=<int>&b=<int>` | business endpoint (bad input → 422) |
| `GET /error` | deliberate 500 (exercises error metrics + stack-trace log) |
| `GET /metrics` | Prometheus scrape target |

## Run order

```bash
# 1. Build + start the whole stack
docker compose up -d --build

# 2. Confirm app metrics endpoint
curl -s http://localhost:8000/metrics | grep http_requests_total

# 3. Generate traffic (mix of healthy + 422/404/500). Args: URL TOTAL CONCURRENCY
./scripts/generate-load.sh http://localhost:8000 800 25

# 4. Prometheus — target should be UP
open http://localhost:9090/targets        # or: curl -s 'http://localhost:9090/api/v1/targets?state=active'

# 5. Grafana — login admin / admin
open http://localhost:3000                 # dashboard: "D6 Observability — Service Telemetry"
```

## Verify (scripted, no browser)

```bash
# Prometheus target UP
curl -s 'http://localhost:9090/api/v1/targets?state=active'
# Live rate by status_code
curl -s 'http://localhost:9090/api/v1/query' \
  --data-urlencode 'query=sum by (status_code) (rate(http_requests_total{service="d6-sample"}[1m]))'
# Same query through Grafana's datasource proxy (run during load for non-zero data)
curl -s -X POST 'http://admin:admin@localhost:3000/api/ds/query' -H 'Content-Type: application/json' \
  -d '{"queries":[{"refId":"A","datasource":{"type":"prometheus","uid":"prometheus"},"expr":"sum by (status_code) (rate(http_requests_total{service=\"d6-sample\"}[1m]))","instant":true}]}'
```

## Tests (no stack needed)

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
python -m pytest tests/ -q
```

## Teardown

```bash
docker compose down -v       # stop + remove containers, network, volumes
```

## Ports

| Service | URL |
|---|---|
| App | http://localhost:8000 (`/metrics`) |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3000 (admin/admin) |
