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
    PROM -->|fire alerts| AM["alertmanager:9093"]
    GRAF["grafana:3000<br/>provisioned dashboard"] -->|datasource proxy| PROM
```

## Layout

```
observability-bolt-on/
├── app/
│   ├── main.py            # FastAPI + observability middleware + /metrics route
│   ├── logging_setup.py   # JSON structured logging (+ trace correlation)
│   ├── metrics.py         # prometheus-client counters + histogram
│   ├── tracing.py         # optional OpenTelemetry tracing (feature-flagged)
│   ├── middleware/security.py  # security response headers
│   └── calc.py
├── tests/                 # pytest (24 tests, ≥80% coverage gate)
├── Dockerfile             # non-root (UID 10001), digest-pinned base
├── docker-compose.yml     # app + prometheus + alertmanager + grafana
├── compose.prod.yml       # prod overlay (no anon, password required, loopback UIs)
├── compose.tracing.yml    # tracing overlay (Jaeger all-in-one)
├── compose.logs.yml       # log overlay (Loki + Promtail)
├── prometheus/
│   ├── prometheus.yml      # scrape + rule_files + alerting
│   ├── alerts.yml          # TargetDown · HighErrorRate · HighLatencyP95
│   └── recording_rules.yml # SLI series for SLO/error-budget
├── alertmanager/alertmanager.yml
├── grafana/provisioning/
│   ├── datasources/        # Prometheus (+ Loki) datasources (as code)
│   └── dashboards/         # file provider + 4-panel dashboard (as code)
├── scripts/
│   ├── generate-load.sh    # mixed-traffic load generator
│   └── verify-stack.sh     # scripted end-to-end stack verification
├── Makefile                # test / lint / typecheck / up / down / verify
├── pytest.ini · ruff.toml · mypy.ini · .env.example
└── docs/
    ├── SLO.md · RUNBOOK.md
    └── agent-analysis/
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

## Profiles (demo vs prod) + overlays

```bash
# Demo (default): admin/admin, anonymous read-only viewer enabled.
docker compose up -d --build

# Prod hardening: no anonymous access, GRAFANA_ADMIN_PASSWORD required,
# Prometheus/Grafana/Alertmanager UIs bound to loopback only.
export GRAFANA_ADMIN_PASSWORD='<strong-password>'
docker compose -f docker-compose.yml -f compose.prod.yml up -d --build

# Optional overlays (compose -f docker-compose.yml -f <overlay> up -d):
#   compose.tracing.yml  → Jaeger + OTEL_ENABLED=true (UI :16686)
#   compose.logs.yml     → Loki + Promtail (Grafana "Loki" datasource)
```

## Alerting

Prometheus evaluates [`prometheus/alerts.yml`](prometheus/alerts.yml) and routes
firing alerts to Alertmanager:

| Alert | Condition |
|---|---|
| `TargetDown` | `up{job="d6-app"} == 0` for 30s |
| `HighErrorRate` | 5xx ratio > 5% for 2m |
| `HighLatencyP95` | p95 latency > 500ms for 5m |

```bash
curl -s http://localhost:9090/api/v1/rules        # rules loaded
curl -s http://localhost:9093/api/v2/alerts | jq . # active alerts in Alertmanager
```

SLOs + error-budget policy: [`docs/SLO.md`](docs/SLO.md) · triage: [`docs/RUNBOOK.md`](docs/RUNBOOK.md)

## Tests + quality gates (no stack needed)

```bash
make check          # ruff + mypy --strict + pytest (coverage ≥80%, zero warnings)
# or manually:
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
ruff check . && ruff format --check . && mypy app --strict && pytest
```

## End-to-end stack verification

```bash
./scripts/verify-stack.sh    # build → load → assert target UP + PromQL non-empty + rules loaded
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
| Alertmanager | http://localhost:9093 |
| Grafana | http://localhost:3000 (admin/admin — demo default) |
