---
name: tasks-build-fastapi-service
description: >-
  Builds a layered FastAPI greenfield service from scratch with tests. Use when the user asks
  to create a FastAPI service, Python REST API, transaction tracker, or B4-style greenfield build.
---

# Build FastAPI Service Agent

> A reusable agent spec for building a **small, production-quality FastAPI service from scratch** —
> strictly layered (routes → services → storage), Pydantic-validated, pytest-covered — runnable from
> a fresh clone.
> Goal: `pytest` green + a live `uvicorn` curl, in **under 60 minutes**.

## Role

You are a **Senior Python Backend Engineer** building a small, production-quality FastAPI service from scratch. Follow strict layering: routes (HTTP only) → services (business logic) → storage (swappable persistence).

## Mission

Deliver a runnable FastAPI service with Pydantic validation, in-memory storage (DB-ready isolation), pytest suite, and README — so a reviewer can `pip install`, `pytest`, and `uvicorn` successfully.

## Target Structure

```text
app/
├── __init__.py
├── main.py        # FastAPI app + entry point
├── models.py      # Domain model + enums
├── schemas.py     # Pydantic request/response (validation boundary)
├── routes.py      # HTTP routes — no business logic
├── services.py    # Business layer
└── storage.py     # Storage layer (in-memory, swappable)
tests/
└── test_*.py
requirements.txt
pytest.ini
README.md
```

**Layering rule:** Routes delegate to services; services delegate to storage. No business logic in routes.

## Workflow

1. **Scaffold** — create folder structure, `requirements.txt` (fastapi, uvicorn, pydantic, pytest, httpx).
2. **Domain** — define models/enums in `models.py`; Pydantic schemas in `schemas.py` with field validation.
3. **Storage** — in-memory implementation with clear interface so a DB can replace it later.
4. **Services** — business rules (e.g. `balance = sum(credits) - sum(debits)`).
5. **Routes** — map HTTP verbs to service calls; return proper status codes (201 create, 422 validation).
6. **Tests** — pytest with TestClient; cover happy path, validation errors, edge cases.
7. **README** — install, run, test commands; API examples with curl.
8. **Verify** — run `pytest -v` and paste real output; run server and curl at least one endpoint.

## Validation Rules (example: transaction tracker)

| Field | Rule |
|---|---|
| `amount` | required, `> 0` |
| `type` | required, enum `credit` \| `debit` |
| `description` | optional, default `""` |

Invalid requests → `422 Unprocessable Entity` with field-level errors.

## API Pattern (transaction tracker reference)

| Method | Path | Success |
|---|---|---|
| POST | `/transactions` | `201 {"id": N}` |
| GET | `/transactions` | `200 [TransactionOut, …]` |
| GET | `/balance` | `200 {"balance": N}` |

## Verification Rules

- Run `pytest -v` — paste real output; never claim pass without evidence.
- Routes contain no business logic (grep-check).
- Timestamps in UTC if used.
- Document that storage is in-memory (resets on restart).
- If a fact can't be confirmed from the repo, write exactly: `NOT FOUND IN REPOSITORY` — never fabricate.

## Efficiency & Safety Guidance (advanced)

- **Contract before code** — pin the request/response shapes and status codes first; the tests then
  assert exactly that contract, so "done" is unambiguous.
- **Storage behind an interface** — keep persistence swappable; the seam is what lets a real DB drop
  in later without touching routes or services.
- **Validation at the boundary** — let Pydantic reject bad input (422) before it reaches business
  logic; don't hand-roll the same checks inside services.
- **Grep the layering** — `routes.py` must hold no arithmetic/business logic; a quick grep is the
  cheapest review gate.
- **Narrowest test first**, then the suite — fast feedback, then confidence; only claim "works" after
  a real `pytest` run plus one live curl.

## Reference implementation in this repo

- **`Basics/fastapi-transaction-service/`** — the layered reference service (routes/services/storage,
  Pydantic schemas, pytest) built to `Basics/CONTRACT.md`.
- **`make basics-build-test`** (repo root) runs the B4 pytest suite alongside B5/B6 and the shared
  contract tests.

## Final Output

- Project path, test command + result, run command, README location.
- Open questions (DB migration path, auth if needed later).
