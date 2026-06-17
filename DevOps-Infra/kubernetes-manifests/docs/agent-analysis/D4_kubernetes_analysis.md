# D4 — Phase 1: Repository Analysis & Workspace Audit

Every runtime decision below is backed by a **file-level proof source**. No assumptions.

## Workload selected

The deployed workload reuses the **D3 FastAPI service** core (`/health`, `/add`), kept
self-contained inside `D4/` so the task is reproducible independently. It is enhanced
minimally for a production Kubernetes posture: a dedicated readiness endpoint and
ConfigMap-driven configuration.

| Concern | Decision | Evidence (file) |
|---|---|---|
| Language / runtime | Python 3.12 | `Dockerfile:1` → `FROM python:3.12-slim` |
| Web framework | FastAPI + Uvicorn (ASGI) | `requirements.txt:1-2`; `app/main.py:9` |
| Startup command | `uvicorn app.main:app --host 0.0.0.0 --port 8000` | `Dockerfile:21` (CMD) |
| Listen port | `8000` | `Dockerfile:16` (`EXPOSE 8000`); `app/main.py` uvicorn args |
| Liveness signal | `GET /health` → `{"status":"ok"}` | `app/main.py:36-39` |
| Readiness signal | `GET /ready` → `{"status":"ready"}` | `app/main.py:42-45` |
| Business endpoint | `GET /add?a=<int>&b=<int>` | `app/main.py:48-51` |
| Config surface | `GET /` echoes injected env | `app/main.py:29-32` |
| Required env vars | `APP_ENV`, `APP_GREETING`, `APP_VERSION` (all have defaults) | `app/main.py:23-25` (`os.getenv`) |
| State | **Stateless** — in-memory only, no DB/volume for app data | `app/` (no persistence code) |
| User | Non-root, uid `10001` | `Dockerfile:18-19` (`useradd ... 10001`, `USER 10001`) |
| Filesystem writes | None at app level (`PYTHONDONTWRITEBYTECODE=1`) → `readOnlyRootFilesystem` safe; `/tmp` mounted writable as defense in depth | `Dockerfile:3`; `k8s/deployment.yaml` (emptyDir `/tmp`) |

## Compute sizing rationale

A minimal FastAPI/Uvicorn process idles at a few tens of MB RSS. Chosen Kubernetes
allocations (`k8s/deployment.yaml`):

- **requests** `cpu: 50m`, `memory: 64Mi` — schedulable on any node, honest baseline.
- **limits** `cpu: 250m`, `memory: 128Mi` — headroom for burst without starving the node.

## Probe mapping rationale

- **startupProbe** → `/health` (30 × 2s = up to 60s grace) so slow cold starts never trip
  the liveness probe.
- **livenessProbe** → `/health` — restart the container only if the process is wedged.
- **readinessProbe** → `/ready` — gate Service traffic; distinct path so readiness and
  liveness can diverge in the future without code changes.

## Networking decision

- **Service:** `ClusterIP` on port `80` → `targetPort: http` (8000). Internal-stable VIP;
  the network proof uses `kubectl port-forward` (no controller dependency).
- **Ingress:** included (`k8s/ingress.yaml`) and dry-run validated, marked **optional** —
  it requires an ingress controller; not on the critical proof path.

## Image delivery into kind

The image is built locally and **side-loaded** with `kind load docker-image` (no registry).
The Deployment therefore sets `imagePullPolicy: IfNotPresent` so the kubelet uses the
side-loaded image instead of attempting a registry pull.
