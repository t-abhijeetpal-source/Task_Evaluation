# I5 — Dockerized Currency Conversion Service

A FastAPI currency-conversion service, containerized. Exposes `POST /convert` and `GET /health`.

> **Verification status:** ✅ Built, run, and verified in Docker (Colima). Image
> `currency-service:1.0` (55 MB content) builds; container runs **Up (healthy)**; `/health`→ok,
> `/convert`→8300, unsupported→400. Full evidence in `VERIFICATION_RESULTS.md`.
> (On this corporate network the Colima VM needed the corporate root CA trusted to pull the base
> image — documented in VERIFICATION_RESULTS.md.)

---

## Prerequisites

A working Docker engine. On macOS via Colima (already installed here):

```bash
colima start            # starts the Linux VM that backs Docker
docker info             # should print engine details
```

## Build

```bash
cd I5
docker build -t currency-service:1.0 .
```

## Run

```bash
docker run -d --name currency -p 8000:8000 currency-service:1.0
docker ps                       # container should be "Up (healthy)" after ~5s
```

## Verification

```bash
# health
curl localhost:8000/health
# -> {"status":"ok"}

# conversion
curl -X POST localhost:8000/convert -H 'Content-Type: application/json' \
  -d '{"amount":100,"from":"USD","to":"INR"}'
# -> {"converted_amount":8300,"from":"USD","to":"INR"}

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

## Configuration

| Env var | Default | Purpose |
|---|---|---|
| `PORT` | `8000` | Port uvicorn binds inside the container |

```bash
docker run -d --name currency -e PORT=9000 -p 9000:9000 currency-service:1.0
```

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `Cannot connect to the Docker daemon` | engine not running | `colima start` (macOS) / start Docker Desktop |
| `no space left on device` during build/VM start | disk full | free several GB, then `colima start` |
| container exits immediately | bad start command / import error | `docker logs currency` |
| `curl: connection refused` | port not published / app still starting | check `-p 8000:8000`; wait for `healthy` |
| health shows `unhealthy` | `/health` not responding | `docker logs currency`; verify `PORT` matches `-p` |
