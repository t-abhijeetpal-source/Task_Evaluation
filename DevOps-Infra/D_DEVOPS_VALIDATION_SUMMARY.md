# DevOps & Infra (D1–D6) — Validation & Hardening Summary

Run date: **2026-06-17**. Every task was executed and validated independently against
its source document requirement ("artifacts that not only parse, but actually run
end-to-end with proof"). Gaps found during validation were fixed and re-verified.

## Status matrix

| Task | Deliverable | Validated by (real execution) | Result |
|---|---|---|---|
| **D1** | Terraform: Lambda + API Gateway + S3 | `terraform fmt -check` · `init` · `validate` · `plan` (offline, mock creds) | ✅ valid; **plan = 15 add / 0 change / 0 destroy** |
| **D2** | docker-compose: API + Postgres + worker | `up --build` → auto-seed → `integration-test.sh` → `down -v` → **clean re-up from zero** | ✅ e2e **PASS**, 0 schema errors after fix |
| **D3** | CI pipeline (lint/test/build/image) | `run-ci-local.sh` (5 stages) + documented failure-mode demo | ✅ **ALL STAGES PASSED** |
| **D4** | Kubernetes on kind | `kubectl apply` → rollout 2/2 → `curl` proofs → browser screenshot | ✅ 2/2 Running, 0 restarts |
| **D5** | Reproducible env from fresh clone | `make` from a simulated fresh clone (rsync, no `.venv`) | ✅ **4 tests pass**, pinned Python 3.12.8 |
| **D6** | Observability (logs + metrics + Grafana) | load → `/metrics` → Prometheus UP → Grafana live panels (screenshot) | ✅ live dashboard, 7.28K reqs |

## Gaps found and fixed during this pass

1. **D2 — broken "clean re-up from zero" (real defect).** The worker crash-looped with
   `relation "jobs" does not exist` until `seed.sh` was run by hand; a fresh `up` had no
   schema. **Fix:** mounted the idempotent `database/seed.sql` into Postgres's
   `/docker-entrypoint-initdb.d/` so schema auto-applies on a fresh DB. **Re-verified:**
   `down -v` → `up` → integration test PASS with **0** schema errors, no manual seed.

2. **D5 — implicit `gpg` dependency (real defect).** First fresh-clone bootstrap failed:
   mise couldn't install Python because GitHub attestation verification needs `gpg`, which
   is absent on a clean machine. **Fix:** `python.github_attestations = false` in `mise.toml`
   (checksums still verified). **Re-verified:** fresh-clone `make` succeeds end-to-end.

3. **D6 — load generator never hit the 500 path (caught earlier).** `case 9` used
   `n % 2 == 0` to split 500/404, but numbers ending in 9 are always odd. **Fixed** to
   tens-digit parity; re-run produced `500=40, 404=40`.

## Browser screenshots of running hosts (`<task>/screenshots/`)

| Host | Screenshot |
|---|---|
| Grafana dashboard (live panels) | `D6/screenshots/grafana-dashboard.png` |
| Prometheus targets (both UP) | `D6/screenshots/prometheus-targets.png` |
| Prometheus graph (live PromQL) | `D6/screenshots/prometheus-graph.png` |
| D6 app Swagger + `/metrics` | `D6/screenshots/app-docs.png`, `app-metrics.png` |
| D2 Jobs API Swagger + `/jobs` | `D2/screenshots/api-swagger-docs.png`, `api-jobs-json.png` |
| D4 service on kind (Swagger + ConfigMap root) | `D4/screenshots/service-swagger-docs.png`, `service-root-configmap.png` |
| D3 service container (Swagger + `/add`) | `D3/screenshots/service-swagger-docs.png`, `add-endpoint-json.png` |

(D1 is serverless Terraform — no running host to screenshot; proof is the `plan` output.)

## Key artifacts saved per folder

- **D1:** `docs/agent-analysis/D1_terraform_plan_output.txt`, `D1_terraform_validation.md`
- **D2:** `docs/agent-analysis/D2_validation_and_hardening.md`, `D2_compose_e2e_record.md`
- **D3:** `docs/agent-analysis/D3_ci_pipeline_record.md`
- **D4:** `docs/agent-analysis/D4_kubernetes_analysis.md`, `D4_kubernetes_validation_record.md`
- **D5:** `docs/agent-analysis/D5_reproducibility_record.md`, `D5_bootstrap_output.txt`
- **D6:** `docs/agent-analysis/D6_service_analysis.md`, `D6_observability_record.md`

## How to reproduce each
```bash
# D1
cd D1 && terraform init && terraform validate && terraform plan
# D2
cd D2 && docker compose up -d --build && ./scripts/integration-test.sh && docker compose down -v
# D3
cd D3 && bash scripts/run-ci-local.sh
# D4
cd D4 && kind create cluster --name d4-cluster && docker build -t d4-sample:v1 . \
  && kind load docker-image d4-sample:v1 --name d4-cluster && kubectl apply -f k8s/
# D5
cd D5 && make
# D6
cd D6 && docker compose up -d --build && ./scripts/generate-load.sh http://localhost:8000 800 25
```

## Running state at end of this pass
- D6 stack (`d6-app`, `d6-prometheus`, `d6-grafana`) — **up** (Grafana anon-viewable at :3000).
- D2 stack — **up** (API at :8080).
- D4 kind cluster `d4-cluster` — **up** (2/2 pods).
Tear down: `docker compose down -v` in D2 and D6; `kind delete cluster --name d4-cluster`.
