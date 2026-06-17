# B4 — FastAPI Greenfield Service

> Build report for the lightweight transaction tracking service.
> Status: **BUILT, TESTED, AND VERIFIED RUNNING.**

---

## Architecture

Three strictly separated layers, dependencies pointing inward:

```text
HTTP request
   │
   ▼
API layer        app/routes.py      route handlers, no business logic
   │             app/main.py        FastAPI app + entry point
   ▼
Business layer   app/services.py    create / list / balance logic
   │
   ▼
Storage layer    app/storage.py     in-memory store (swappable)

Cross-cutting:   app/schemas.py     Pydantic validation (API boundary)
                 app/models.py      domain model + TransactionType enum
```

- **No business logic in routes** — each endpoint delegates to `TransactionService`.
- **Dependency injection** — routes get the service via FastAPI `Depends(get_service)`, which
  makes the service/store easy to substitute in tests.
- **Storage is isolated** — swapping `InMemoryStorage` for a DB requires no route/service rewrite.

---

## API Design

| Method | Route | Handler (`app/routes.py`) | Request | Response |
|---|---|---|---|---|
| POST | `/transactions` | `create_transaction` | `{amount, type, description?}` | `201 {"id": 1}` |
| GET | `/transactions` | `list_transactions` | — | `200 [TransactionOut, ...]` |
| GET | `/balance` | `get_balance` | — | `200 {"balance": <number>}` |
| GET | `/health` | `health` | — | `200 {"status":"ok"}` |

`balance = sum(credits) - sum(debits)` — implemented in `TransactionService.get_balance`.

---

## Validation Strategy

Enforced declaratively by Pydantic v2 in `app/schemas.py`:

- `amount: float = Field(..., gt=0)` → rejects zero/negative amounts.
- `type: TransactionType` (str Enum `credit`/`debit`) → rejects any other value.
- `description: Optional[str]` defaulting to `""` → optional.

Invalid payloads never reach the service; FastAPI returns `422 Unprocessable Entity` with a
field-level error body automatically.

---

## Test Results

**Command:** `python -m pytest -v`

```text
============================= test session starts ==============================
platform darwin -- Python 3.9.6, pytest-8.4.2, pluggy-1.6.0
rootdir: /Users/abhijeetpal/Desktop/workspace/Tasks/B4
configfile: pytest.ini
collected 6 items

tests/test_transactions.py::test_create_transaction PASSED               [ 16%]
tests/test_transactions.py::test_list_transactions PASSED                [ 33%]
tests/test_transactions.py::test_balance_calculation PASSED              [ 50%]
tests/test_transactions.py::test_balance_empty_is_zero PASSED            [ 66%]
tests/test_transactions.py::test_rejects_non_positive_amount PASSED      [ 83%]
tests/test_transactions.py::test_rejects_invalid_type PASSED             [100%]

============================== 6 passed in 0.68s ===============================
```

**Pass/fail count: 6 passed, 0 failed.**

Coverage of required scenarios:
- Test 1 — create transaction ✓
- Test 2 — list transactions ✓
- Test 3 — balance calculation ✓
- Bonus — empty balance is zero ✓
- Bonus — rejects non-positive amount (422) ✓
- Bonus — rejects invalid type (422) ✓

### Live server verification

Server started with `uvicorn app.main:app --port 8077`, then:

```text
GET  /health                          -> {"status":"ok"}
POST /transactions (credit 100)       -> {"id":1}
POST /transactions (debit 40)         -> {"id":2}
GET  /transactions                    -> [ {id:1,amount:100.0,type:credit,...},
                                           {id:2,amount:40.0,type:debit,...} ]
GET  /balance                         -> {"balance":60.0}      (100 - 40 = 60 ✓)
POST /transactions (amount 0)         -> HTTP 422
POST /transactions (type "transfer")  -> HTTP 422
```

---

## Run Commands

```bash
cd B4
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Run
uvicorn app.main:app --reload          # http://127.0.0.1:8000/docs

# Test
pytest -v
```

---

## Known Limitations

- **In-memory storage** — all data is lost on restart; not safe for multiple processes/workers.
- **No persistence/migrations** — a real DB (e.g. SQLite/Postgres via SQLAlchemy) would replace `storage.py`.
- **No authentication/authorization** — every endpoint is public.
- **No pagination** on `GET /transactions`.
- **Float amounts** — fine for this exercise; production money handling should use `Decimal`.
- **Single currency / no account model** — one global ledger.

---

## Provenance

| Item | Status |
|---|---|
| Application code (`app/`) | **AGENT GENERATED** |
| Tests (`tests/`) | **AGENT GENERATED** |
| README | **AGENT GENERATED** |
| `pytest -v` result (6 passed) | **MANUALLY VERIFIED** — command executed, output captured above |
| Live curl responses + balance math | **MANUALLY VERIFIED** — server run, endpoints called |
