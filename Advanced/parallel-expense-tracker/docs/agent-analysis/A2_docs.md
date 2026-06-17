# A2 — Documentation Deliverables

This note records the user-facing documentation produced for the Expense Tracker
project and what each document covers.

## Documents produced

### `README.md` (project root)
The primary developer-facing document. Covers:
- **Project overview** and feature list (add/list expenses, summary, health).
- **Architecture** as a Mermaid diagram: User → Frontend (`static/`) → FastAPI
  (`app.main:app`) → SQLAlchemy → SQLite (`data/expenses.db`), plus the `GET /`
  static-UI serving path and the router-before-static ordering note.
- **Folder structure** — annotated tree of `app/`, `static/`, `db/`, `data/`,
  `tests/`, Docker files, and CI.
- **Setup** — Python 3.12 venv + `pip install -r requirements.txt`.
- **Run locally** — `uvicorn app.main:app --reload` on http://localhost:8000,
  how to open the UI, `/docs`, and the `DATABASE_URL` config option.
- **Test** — `pytest -v` and how the isolated temp-DB fixture works.
- **Docker** — `docker build` / `docker run` and `docker compose up --build`.
- **API reference table** — method, path, request, response for `/api/health`,
  `/api/expenses` (POST/GET), `/api/summary`, and `/`, with `curl` examples and
  the 422 validation behaviour.
- **CI** — summary of the GitHub Actions test + build jobs.

### `RUNBOOK.md` (project root)
The operations/on-call document. Covers:
- **Start/stop** — local uvicorn (dev + prod-like) and `docker compose`.
- **Health check** — `curl /api/health`, the healthy `{"status":"ok"}` response,
  and how to read Docker health status.
- **Where data lives** — `data/expenses.db`, the Compose bind mount, plus
  **backup/restore** via file copy and `sqlite3 .dump`.
- **Logs** — uvicorn stdout/stderr and `docker compose logs`.
- **Common issues & fixes** — port 8000 in use, missing/unwritable data dir,
  422 errors (positive-amount rule + validation), UI/API connectivity.
- **Rollback strategy** — revert image tag / `git revert`, SQLite restore from
  backup, and the recommended ordered procedure.

## Source of truth

All content was derived by reading the actual implementation: `app/main.py`,
`app/routes.py`, `app/database.py`, `app/models.py`, `app/schemas.py`,
`requirements.txt`, `Dockerfile`, `docker-compose.yml`, `static/index.html`,
`tests/conftest.py`, and `.github/workflows/ci.yml`. Notable facts captured:
default `DATABASE_URL=sqlite:///./data/expenses.db`, the explicit
`422 {"error":"amount must be positive"}` guard, port 8000, the non-root Docker
user, and the persistent `./data` bind mount.

## Agent Generated

These documents (`README.md`, `RUNBOOK.md`, and this analysis file) were generated
by an AI agent (Claude, Documentation Engineer role) as part of a parallel build.
They reflect the repository state at authoring time and should be reviewed by a
human before being relied upon in production.
