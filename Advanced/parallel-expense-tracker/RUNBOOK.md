# Expense Tracker — Operations Runbook

Operational guide for running, monitoring, and recovering the Expense Tracker
service. For project/architecture details see `README.md`.

Service summary: FastAPI app (`app.main:app`) serving the UI at `/` and the JSON
API at `/api/*`, backed by SQLite at `data/expenses.db`. Default port: **8000**.

---

## 1. Start / stop

### Local (uvicorn)

Start (development, auto-reload):

```bash
source .venv/bin/activate
uvicorn app.main:app --reload
```

Start (no reload, closer to production):

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Stop: press `Ctrl+C` in the terminal running uvicorn. If it was backgrounded:

```bash
pkill -f "uvicorn app.main:app"
```

### Docker Compose

Start (build + run, detached):

```bash
docker compose up -d --build
```

Stop (keep the data volume):

```bash
docker compose down
```

Stop and **delete** containers; the SQLite file persists because it is bind-mounted
to `./data` on the host (only removing that directory loses data).

Restart just the app:

```bash
docker compose restart app
```

---

## 2. Health check

```bash
curl http://localhost:8000/api/health
```

Healthy response:

```json
{"status":"ok"}
```

HTTP status `200` with `{"status":"ok"}` = service up **and** the database is
reachable (the endpoint runs a `SELECT 1` round-trip). If the DB is unreachable
the endpoint returns `503 {"status":"unavailable",...}`, which the Docker/Compose
HEALTHCHECK treats as unhealthy.

- The Docker image and Compose service both define a `HEALTHCHECK` that polls
  `/api/health` every 30s. Check container health with:

  ```bash
  docker compose ps          # STATUS column shows "healthy" / "unhealthy"
  docker inspect --format '{{.State.Health.Status}}' <container>
  ```

- A connection refused / timeout means the process is down or the port is wrong.
- A `200` confirms the DB is **readable** (`SELECT 1`); to confirm it is
  **writable**, POST an expense (`201`) or `GET /api/expenses` (`200` + array).

---

## 3. Where data lives

- **File:** `data/expenses.db` (SQLite). Path is controlled by `DATABASE_URL`
  (default `sqlite:///./data/expenses.db`).
- **Docker:** the host directory `./data` is bind-mounted to `/app/data` in the
  container (see `docker-compose.yml`), so the database survives container
  restarts and rebuilds.

### Backup

The simplest reliable backup is a file copy while the app is idle/stopped:

```bash
cp data/expenses.db "backups/expenses-$(date +%Y%m%d-%H%M%S).db"
```

For a portable, human-readable logical backup (safe while running):

```bash
sqlite3 data/expenses.db ".dump" > "backups/expenses-$(date +%Y%m%d-%H%M%S).sql"
```

### Restore

From a file copy:

```bash
# stop the app first (Ctrl+C / docker compose down)
cp backups/expenses-YYYYMMDD-HHMMSS.db data/expenses.db
# restart the app
```

From a `.dump` SQL file:

```bash
rm -f data/expenses.db
sqlite3 data/expenses.db < backups/expenses-YYYYMMDD-HHMMSS.sql
```

Always stop the service before overwriting the DB file to avoid corruption.

---

## 4. Logs

- **Local (uvicorn):** logs go to **stdout/stderr** in the terminal running
  uvicorn (startup banner, access lines, tracebacks). Redirect to a file if needed:
  `uvicorn app.main:app >> app.log 2>&1`.
- **Docker:**

  ```bash
  docker compose logs -f app        # follow
  docker compose logs --tail=200 app
  docker logs <container-id>
  ```

There is no separate log file or log-rotation configured; rely on the terminal,
the container log driver, or your process manager (systemd, etc.).

---

## 5. Common issues & fixes

### Port 8000 already in use

Symptom: `[Errno 48] Address already in use` (macOS) / `Address already in use`.

```bash
lsof -i :8000              # find the PID using the port
kill <PID>                 # or kill -9 <PID>
# or run on a different port:
uvicorn app.main:app --port 8001
```

For Docker, change the host side of the mapping in `docker-compose.yml`
(`"8001:8000"`).

### Missing / unwritable data directory

Symptom: `sqlite3.OperationalError: unable to open database file`.

- The app auto-creates `./data` only when `DATABASE_URL` is the default value. If
  you set a custom `DATABASE_URL`, ensure the target directory exists and is
  writable: `mkdir -p data && chmod u+rw data`.
- In Docker, ensure the host `./data` directory exists and is writable by UID
  `1000` (the container's `appuser`): `mkdir -p data`.

### 422 errors when creating an expense

- `{"error":"amount must be positive"}` → the `amount` was `<= 0`. Send a positive
  number.
- Validation `422` (`detail` array) → the body is malformed: missing
  `amount`/`category`, wrong types, missing `Content-Type: application/json`, or
  an `amount` that is non-finite (NaN/Infinity), has more than 2 decimal places,
  or exceeds 1e10. Verify the payload matches `{"amount":number,"category":str,"note"?:str}`
  (see `CONTRACT.md`).

### UI loads but data does not update / API calls fail

- Confirm the API is reachable: `curl http://localhost:8000/api/health`.
- Check the browser devtools Network tab for failing `/api/*` calls and inspect
  uvicorn/container logs for tracebacks.

---

## 6. Rollback strategy

### Code / image rollback

- **Docker (tagged images):** redeploy a known-good tag.

  ```bash
  docker pull <registry>/expense-tracker:<previous-tag>
  # update the image tag in docker-compose.yml, then:
  docker compose up -d
  ```

- **Source (git):** revert the offending change and redeploy.

  ```bash
  git revert <bad-commit-sha>     # or: git checkout <last-good-tag>
  # reinstall deps if requirements changed, then restart the service
  ```

### Data rollback

If a deploy or bad write corrupted/changed data, restore the most recent good
backup (see section 3):

```bash
docker compose down               # or stop uvicorn
cp backups/expenses-<good>.db data/expenses.db
docker compose up -d              # or restart uvicorn
```

### Recommended order

1. Stop the service.
2. Roll back the code/image to the last known-good version.
3. Restore the database from backup if data was affected.
4. Start the service and verify with the health check **and** a `GET /api/expenses`.

---

> _Runbook generated by an AI agent (Claude). Verify each procedure in a safe
> environment before using it during a real incident._
