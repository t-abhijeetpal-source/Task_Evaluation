# D6 Observability — Operational Runbook

Operating guide for the observability bolt-on stack: how to start it, drive it,
read the signals, triage alerts, and tear it down.

## Components

| Service | Port | Role |
|---|---|---|
| `d6-app` | 8000 | Instrumented FastAPI service (`/metrics`, JSON logs) |
| `d6-prometheus` | 9090 | Scrapes the app every 5s; evaluates alert + recording rules |
| `d6-alertmanager` | 9093 | Receives + groups fired alerts |
| `d6-grafana` | 3000 | Dashboards-as-code over the Prometheus datasource |
| `d6-jaeger` *(tracing overlay)* | 16686 | Trace UI (only with `compose.tracing.yml`) |
| `d6-loki` / `d6-promtail` *(logs overlay)* | 3100 | Log aggregation (only with `compose.logs.yml`) |

## 1. Startup

```bash
# Demo profile (admin/admin, anonymous viewer enabled)
docker compose up -d --build

# Production profile (no anonymous, password required, UIs on loopback)
export GRAFANA_ADMIN_PASSWORD='<strong-password>'
docker compose -f docker-compose.yml -f compose.prod.yml up -d --build
```

Wait for health: `docker compose ps` should show `d6-app` as `Up (healthy)`.

## 2. Load test

```bash
# Args: BASE_URL TOTAL CONCURRENCY  (mix of 200/422/404/500)
./scripts/generate-load.sh http://localhost:8000 600 20
```

## 3. Reading the signals

### Dashboard
Grafana → **"D6 Observability — Service Telemetry"** (`http://localhost:3000`):
request rate by status_code, error rate, p50/p95/p99 latency, total requests.

### Raw metrics
```bash
curl -s http://localhost:8000/metrics | grep -E 'http_requests_total|http_request_errors_total'
```

### Log field reference
Each request emits one JSON line on the app's stdout (`docker compose logs -f app`):

| Field | Meaning |
|---|---|
| `timestamp` | ISO-8601 UTC |
| `level` | `INFO` (completed) / `ERROR` (failed) |
| `message` | `request_completed` or `request_failed` |
| `request_id` | per-request id, also returned as `X-Request-ID` |
| `method`, `path` | HTTP verb + **route template** (low cardinality) |
| `status_code` | response status |
| `duration_ms` | server-side handling time |
| `client` | peer IP |
| `error` | stack trace (only on `request_failed`) |
| `trace_id`, `span_id` | present only when tracing is enabled |

`path` is always the matched route (`/add`, not `/add?a=1`); unmatched URLs
collapse to `/_unmatched` to protect metric cardinality.

## 4. Alert triage

Active alerts: Prometheus `http://localhost:9090/alerts`, or Alertmanager
`curl -s http://localhost:9093/api/v2/alerts | jq .`

| Alert | Likely cause | First steps |
|---|---|---|
| **TargetDown** | app crashed / OOM / network | `docker compose ps`; `docker compose logs app`; check container memory limit (256M) |
| **HighErrorRate** (5xx > 5%) | unhandled exceptions | grep logs for `request_failed` + `error` stack traces; find the failing `path` |
| **HighLatencyP95** (> 500ms) | downstream slowness / saturation | inspect latency panel by `path`; check CPU limit; correlate with traffic spike |

See [`SLO.md`](SLO.md) for the objectives and error-budget policy behind these.

## 5. Distributed tracing (optional)

```bash
docker compose -f docker-compose.yml -f compose.tracing.yml up -d --build
./scripts/generate-load.sh http://localhost:8000 200 10
open http://localhost:16686        # Jaeger UI → service "d6-sample"
```
Correlate a slow trace to its logs via the shared `trace_id` field.

## 6. Log aggregation (optional, Loki)

```bash
docker compose -f docker-compose.yml -f compose.logs.yml up -d
# Grafana → Explore → "Loki" datasource:
#   {container="d6-app"} | json                          # all structured logs
#   {container="d6-app"} | json | status_code=`500`      # only failures
#   {container="d6-app"} | json | line_format "{{.request_id}} {{.path}} {{.duration_ms}}ms"
```

## 7. Common failures

| Symptom | Cause | Fix |
|---|---|---|
| Grafana panels empty | queried after load stopped (`rate[1m]` decayed) | run a query *during* continuous load, or widen the range |
| Prometheus target DOWN | app not healthy yet | wait for healthcheck; `docker compose logs app` |
| `/docs` blank | strict CSP from a proxy | the app omits CSP for this reason; check any fronting proxy |
| Tracing shows no spans | `OTEL_ENABLED` not set | use the tracing overlay (sets it to `true`) |

## 8. Teardown

```bash
docker compose down -v        # add `-f compose.<overlay>.yml` for any overlay you started
```

## 9. Scripted verification

```bash
./scripts/verify-stack.sh     # build → load → assert target UP + PromQL non-empty + rules loaded
```
