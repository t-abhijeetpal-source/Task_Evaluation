# D6 Service-Level Objectives

These SLOs make the observability stack *actionable*: every objective below maps
to a metric the app already exports and to a recording rule in
[`prometheus/recording_rules.yml`](../prometheus/recording_rules.yml). The alert
rules in [`prometheus/alerts.yml`](../prometheus/alerts.yml) fire as the budget
burns.

> Targets are illustrative for a demo service — tune them to real traffic before
> using in production.

## SLIs and SLOs

| SLI | Definition | SLO (28-day window) |
|---|---|---|
| **Availability** | fraction of requests **not** returning 5xx | **≥ 99.5%** |
| **Latency (p95)** | 95th-percentile request duration | **≤ 500 ms** |

### Availability

- **Good events:** `http_requests_total` where `status_code` is not 5xx.
- **Bad events:** `http_request_errors_total{status_code=~"5.."}`.
- **SLI (recording rule):** `job:slo_availability:ratio5m`
  ```promql
  1 - (
    sum(rate(http_request_errors_total{service="d6-sample",status_code=~"5.."}[5m]))
    / clamp_min(sum(rate(http_requests_total{service="d6-sample"}[5m])), 0.001)
  )
  ```
  > 4xx (client errors, e.g. the 422 validation path) are deliberately **not**
  > counted against availability — a bad request is not a service failure.

### Latency

- **SLI (recording rule):** `job:http_request_latency:p95_5m`
  ```promql
  histogram_quantile(0.95,
    sum by (le) (rate(http_request_duration_seconds_bucket{service="d6-sample"}[5m])))
  ```

## Error budget

A 99.5% availability SLO permits **0.5%** of requests to fail over the window.

- **Budget remaining** (fraction of the allowed error rate still unspent):
  ```promql
  1 - (
    (1 - job:slo_availability:ratio5m) / 0.005
  )
  ```
  `1.0` = full budget; `0` = budget exhausted; `< 0` = SLO breached.

### Burn-rate policy

| Burn rate (vs. budget) | Meaning | Action |
|---|---|---|
| > 14.4× over 1h | budget gone in ~2 days | page (critical) |
| > 6× over 6h | budget gone in ~5 days | page (warning) |
| ≤ 1× | sustainable | no action |

`HighErrorRate` (5xx ratio > 5% for 2m) is the fast-burn guardrail wired today;
add multi-window burn-rate alerts from the table above as traffic grows.

## Dashboard

The provisioned Grafana dashboard surfaces request rate, error rate, and
p50/p95/p99 latency. An **error-budget** stat panel can be added with:

```promql
1 - ((1 - job:slo_availability:ratio5m) / 0.005)
```
