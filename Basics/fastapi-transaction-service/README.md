# Transaction Tracking Service (B4 — FastAPI Greenfield)

A lightweight transaction tracking system built with FastAPI. It records credit/debit
transactions and computes a running balance.

`balance = sum(credits) - sum(debits)`

---

## Project Structure

```text
B4/
├── app/
│   ├── __init__.py
│   ├── main.py        # FastAPI app + entry point (API layer)
│   ├── models.py      # Domain model + TransactionType enum
│   ├── schemas.py     # Pydantic request/response schemas (validation)
│   ├── routes.py      # HTTP routes (no business logic)
│   ├── services.py    # Business layer (create/list/balance)
│   └── storage.py     # Storage layer (in-memory, swappable)
├── tests/
│   └── test_transactions.py
├── requirements.txt
├── pytest.ini
└── README.md
```

**Layering:** API (`routes.py`) → Business (`services.py`) → Storage (`storage.py`).
Routes contain no business logic; they delegate to the service.

---

## Installation

```bash
cd B4
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
source .venv/bin/activate
uvicorn app.main:app --reload
```

Then open the interactive docs at <http://127.0.0.1:8000/docs>.

## Test

```bash
source .venv/bin/activate
pytest -v
```

---

## API

### POST /transactions

Create a transaction.

**Request**
```json
{ "amount": 100, "type": "credit", "description": "salary" }
```

**Response** `201 Created`
```json
{ "id": 1 }
```

### GET /transactions

List all transactions.

**Response** `200 OK`
```json
[
  {
    "id": 1,
    "amount": 100.0,
    "type": "credit",
    "description": "salary",
    "timestamp": "2026-06-16T09:35:57.701020Z"
  }
]
```

### GET /balance

**Response** `200 OK`
```json
{ "balance": 500 }
```

---

## Example Requests

```bash
# Create a credit
curl -X POST localhost:8000/transactions \
  -H 'Content-Type: application/json' \
  -d '{"amount":100,"type":"credit","description":"salary"}'
# -> {"id":1}

# Create a debit
curl -X POST localhost:8000/transactions \
  -H 'Content-Type: application/json' \
  -d '{"amount":40,"type":"debit","description":"lunch"}'
# -> {"id":2}

# List
curl localhost:8000/transactions

# Balance
curl localhost:8000/balance
# -> {"balance":60.0}

# Invalid (amount must be > 0) -> 422
curl -X POST localhost:8000/transactions \
  -H 'Content-Type: application/json' \
  -d '{"amount":0,"type":"credit"}'

# Invalid (type must be credit|debit) -> 422
curl -X POST localhost:8000/transactions \
  -H 'Content-Type: application/json' \
  -d '{"amount":50,"type":"transfer"}'
```

---

## Validation

Validation is enforced by Pydantic at the API boundary (`app/schemas.py`):

| Field | Rule |
|---|---|
| `amount` | required, `> 0` |
| `type` | required, must be `credit` or `debit` |
| `description` | optional (defaults to `""`) |

Invalid requests return `422 Unprocessable Entity` with a field-level error body.

---

## Notes

- Storage is **in-memory** — data resets on restart. The storage layer is isolated, so a
  real database can be added without touching routes or services.
- Timestamps are stored in UTC.
