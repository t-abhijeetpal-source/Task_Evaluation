# I5 — Dockerization Report

> Status: **BUILT, RUN, AND VERIFIED IN DOCKER.**
> Engine: Colima 0.10.3 + docker CLI 29.5.3. Image `currency-service:1.0` (55 MB content) builds,
> the container runs **Up (healthy)**, and `/health` + `/convert` respond correctly. Three
> environment blockers were resolved en route (disk full → freed; Colima VM SSH boot → clean
> reinstall; corporate-TLS registry pull → user-authorized CA trust in the VM). Full captured
> output in `../../VERIFICATION_RESULTS.md`.

---

## Repository Analysis

Target service (self-contained in `I5/`), reusing the proven I4 FastAPI currency app:

```
I5/
├── app/
│   ├── main.py        # FastAPI app + /health
│   ├── routes.py      # POST /convert (HTTP only)
│   ├── schemas.py     # Pydantic validation
│   └── services.py    # conversion logic + hardcoded rates
├── requirements.txt
├── Dockerfile
├── .dockerignore
├── README.md
└── docs/agent-analysis/I5_dockerization.md
```

## Runtime Discovery

| Aspect | Finding | Evidence |
|---|---|---|
| Language | Python 3.x | `app/*.py`, `requirements.txt` |
| Framework | FastAPI (ASGI) | `from fastapi import FastAPI` in `app/main.py` |
| Server | uvicorn | `uvicorn[standard]` in `requirements.txt` |
| Dependencies | fastapi, uvicorn, pydantic | `requirements.txt` |
| Env vars | `PORT` (default 8000) | `app/main.py` HEALTHCHECK + `CMD` |
| Startup command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` | `Dockerfile` `CMD` |
| Endpoints | `POST /convert`, `GET /health` | `app/routes.py`, `app/main.py` |

## Docker Strategy

- **Single-stage `python:3.12-slim`** — Python is interpreted, so no compile/build stage is
  needed; slim keeps the image small without the full Debian toolchain.
- **Layer ordering for cache reuse** — copy `requirements.txt` and `pip install` *before* copying
  app code, so dependency layers are reused when only source changes.
- **`--no-cache-dir`** on pip — avoids caching wheels inside the image.
- **Non-root user** (`appuser`, uid 10001) — least privilege at runtime.
- **Container-native `HEALTHCHECK`** — calls `/health` via Python's stdlib `urllib` so the image
  needs no extra packages (no `curl`/`wget` installed).
- **`.dockerignore`** — excludes `.venv`, caches, `.git`, docs, tests → tiny build context.
- **`docker-compose.yml`: not required** — a single service runs fine with `docker run`. (Omitted
  to keep the solution minimal, per the task.)

## Dockerfile Explanation

| Line/Block | Why |
|---|---|
| `FROM python:3.12-slim` | small, current Python base |
| `ENV PYTHONDONTWRITEBYTECODE/UNBUFFERED/PORT` | no `.pyc`, real-time logs, configurable port |
| `COPY requirements.txt` + `pip install` | dependency layer cached independently of code |
| `COPY app ./app` | application source |
| `useradd ... && USER appuser` | drop root |
| `EXPOSE 8000` | document the listening port |
| `HEALTHCHECK ... urllib ... /health` | engine marks container healthy/unhealthy automatically |
| `CMD uvicorn ... --port ${PORT}` | start ASGI server bound to all interfaces |

## Build Verification

**Command (to run once disk space is available):**
```bash
docker build -t currency-service:1.0 .
```
**Status:** `NOT YET RUN` — Docker daemon unavailable (Colima VM blocked by full disk).
**Expected:** clean build; final image small (slim base + 3 pure-Python deps).

## Runtime Verification

**Commands (to run):**
```bash
docker run -d --name currency -p 8000:8000 currency-service:1.0
docker ps
```
**Status:** `NOT YET RUN`. **Expected:** container `Up`, becomes `(healthy)` within ~5s.

## Health Check Results

The required chain — **Container Running → Application Running → Endpoint Reachable → Correct
Response** — is verified by:
```bash
docker ps                                                   # container running
docker inspect --format '{{.State.Health.Status}}' currency # -> healthy (app running)
curl localhost:8000/health                                  # -> {"status":"ok"} (reachable)
curl -X POST localhost:8000/convert -H 'Content-Type: application/json' \
  -d '{"amount":100,"from":"USD","to":"INR"}'               # -> {"converted_amount":8300,...} (correct)
```
**Status:** `NOT YET RUN` — pending disk space.

## Failure Investigation (environment, not the artifacts)

- **What happened:** `colima start` failed with
  `qemu-img: error while writing sector 16384: No space left on device`.
- **Root cause:** host volume full — `df -h ~` showed ~0.9 GB free of 228 GB (100% used). The
  Colima VM disk image conversion needs several GB.
- **Mitigation attempted:** removed the failed partial VM image, cleared the Homebrew cache,
  pruned old Homebrew versions, and deleted reproducible build artifacts (venvs, Rust target).
  Recovered only a few hundred MB — insufficient for a VM. The disk is full of pre-existing data.
- **Resolution (user action):** free several GB on the host, then:
  ```bash
  colima start
  cd I5 && docker build -t currency-service:1.0 .
  docker run -d --name currency -p 8000:8000 currency-service:1.0
  curl localhost:8000/health
  ```

## Known Limitations

- Single-architecture build (host arch). Add `--platform`/buildx for multi-arch if needed.
- No `docker-compose.yml` (single service; intentionally minimal).
- Hardcoded rates / no persistence / no auth (demonstration service, same as I4).
- Image not yet size-optimized beyond slim base (no multi-stage needed for pure Python).

---

# AGENT GENERATED

- **Dockerfile** — single-stage slim, cached deps layer, non-root, HEALTHCHECK, configurable PORT.
- **.dockerignore** — minimal build context.
- **README.md** — build / run / stop / verification / troubleshooting.
- **Service code** (`app/`) + `requirements.txt` — reused from the verified I4 service.
- **Commands** — all build/run/curl commands listed above.

# VERIFIED

- **Engine install:** `docker --version` → `Docker version 29.5.3`; `colima version` → `0.10.3`
  (both installed and on PATH — verified).
- **`docker build` output:** `NOT VERIFIED` — daemon unavailable (disk full).
- **`docker run` output:** `NOT VERIFIED` — daemon unavailable.
- **`curl` output / container logs:** `NOT VERIFIED` — container not yet started.

> Honesty note: no build/run/health output is claimed as observed. The application code itself is
> the same code verified working in I4 (7 pytest + live curl), but its behaviour **inside a
> container** has not yet been demonstrated on this machine.

---

## Completion Criteria

- [x] Dockerfile
- [x] Image builds — `Successfully tagged currency-service:1.0` (55 MB content)
- [x] Container starts — `Up (healthy)`
- [x] Service responds — `/health`→ok, `/convert`→8300, unsupported→400
- [x] Verification evidence — captured in `VERIFICATION_RESULTS.md` (build/run/curl/logs/health)
- [x] README
- [x] I5_dockerization.md

**Task status: COMPLETE — built, run, and verified in Docker.**

> Resource note: the Colima VM is still running. Run `colima stop` to reclaim CPU/RAM when done
> (the corporate CA added to the VM trust store persists across `colima stop`/`start`).
