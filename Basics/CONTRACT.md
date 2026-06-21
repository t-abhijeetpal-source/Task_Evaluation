# B4 / B5 Shared Transaction API Contract

Both **B4** (`Basics/fastapi-transaction-service`) and **B5** (`Basics/node-transaction-service`)
implement the same REST surface. This document is the single source of truth; behavioral tests
read `Basics/fixtures/transaction-vectors.json`.

## Endpoints

| Method | Path | Success | Response |
|---|---|---|---|
| `GET` | `/health` | 200 | `{ "status": "ok", "service": string, "version": string }` |
| `POST` | `/transactions` | 201 | `{ "id": positive-int }` |
| `GET` | `/transactions` | 200 | `[{ "id", "amount", "type", "description", "timestamp" }, ...]` |
| `GET` | `/transactions?limit=&offset=` | 200 | Paginated slice (default `limit=100`, max `1000`) |
| `GET` | `/balance` | 200 | `{ "balance": number }` — O(1) running total in storage |

## Request body — `POST /transactions`

| Field | Type | Required | Rules |
|---|---|---|---|
| `amount` | number | yes | `> 0`, finite, at most 2 decimal places, `<= 1_000_000_000` |
| `type` | string | yes | `"credit"` or `"debit"` |
| `description` | string | no | max 500 characters; default `""` |

## Balance rule

```
balance = sum(credit amounts) - sum(debit amounts)
```

Arithmetic uses **integer minor units (cents)** internally so results like `0.1 + 0.2 = 0.3`
are exact. Balance is maintained as a **running total** in storage (O(1) read).

## Validation errors

| Condition | HTTP status |
|---|---|
| Invalid JSON body | 400 (B5) / 422 (B4 malformed body) |
| Schema / business rule violation | 422 |

B4 error envelope: `{ "error": "validation_failed", "detail": [...] }`  
B5 error envelope: `{ "errors": ["...", ...] }`

Status codes and balance math must match across implementations; error *shape* may differ.

## Observability

- Every response includes `x-request-id` (generated or echoed from request header).
- Structured JSON request logs on the server.

## Contract tests

```bash
# From repo root
make basics-verify

# Or individually
cd Basics/fastapi-transaction-service && pytest tests/test_contract.py -q
cd Basics/node-transaction-service && npm test -- --testPathPattern=contract
```

## Changing the contract

1. Update this file.
2. Update `Basics/fixtures/transaction-vectors.json`.
3. Update B4 and B5 implementations if needed.
4. Run `make basics-verify`.
