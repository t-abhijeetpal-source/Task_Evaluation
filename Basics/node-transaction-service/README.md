# Transaction Tracker API (B5 — Node.js / Express Greenfield)

A lightweight transaction tracking REST API built with Node.js, Express, and Jest.
It records credit/debit transactions and computes a running balance.

`balance = sum(credits) - sum(debits)`

This is the Node.js counterpart of the B4 FastAPI service — same business rules.

---

## Folder Structure

```text
B5/
├── src/
│   ├── app.js                          # Express app factory (API layer)
│   ├── server.js                       # Entry point (app.listen)
│   ├── routes/transactions.js          # Route definitions
│   ├── controllers/transactionController.js  # HTTP <-> service mapping
│   ├── services/transactionService.js  # Business logic + validation + balance
│   ├── models/transaction.js           # Domain model + valid types
│   └── storage/inMemoryStorage.js      # Storage layer (in-memory, swappable)
├── tests/transactions.test.js          # Jest + supertest
├── package.json
└── README.md
```

**Layering:** Routes → Controllers → Service → Storage. Controllers hold no business logic.

---

## Installation

```bash
cd B5
npm install
```

## Start Server

```bash
npm start                 # http://localhost:3000  (PORT env var to override)
```

## Run Tests

```bash
npm test
```

---

## API

### POST /transactions
**Request**
```json
{ "amount": 100, "type": "credit", "description": "salary" }
```
**Response** `201`
```json
{ "id": 1 }
```

### GET /transactions
**Response** `200`
```json
[
  { "id": 1, "amount": 100, "type": "credit", "description": "salary", "timestamp": "2026-06-16T09:40:33.134Z" }
]
```

### GET /balance
**Response** `200`
```json
{ "balance": 500 }
```

---

## API Examples

```bash
# Create a credit
curl -X POST localhost:3000/transactions \
  -H 'Content-Type: application/json' \
  -d '{"amount":100,"type":"credit","description":"salary"}'
# -> {"id":1}

# Create a debit
curl -X POST localhost:3000/transactions \
  -H 'Content-Type: application/json' \
  -d '{"amount":40,"type":"debit","description":"lunch"}'
# -> {"id":2}

# List
curl localhost:3000/transactions

# Balance
curl localhost:3000/balance
# -> {"balance":60}

# Invalid amount (must be > 0) -> 422
curl -X POST localhost:3000/transactions -H 'Content-Type: application/json' -d '{"amount":0,"type":"credit"}'

# Invalid type (must be credit|debit) -> 422
curl -X POST localhost:3000/transactions -H 'Content-Type: application/json' -d '{"amount":5,"type":"transfer"}'

# Malformed JSON -> 400
curl -X POST localhost:3000/transactions -H 'Content-Type: application/json' -d '{ "amount": 100, "type":'
```

---

## Validation & Status Codes

| Condition | Status |
|---|---|
| Valid transaction | `201` |
| `amount` missing / not a number / `<= 0` | `422` |
| `type` not `credit` or `debit` | `422` |
| Malformed JSON body | `400` |
| Unknown route | `404` |

`description` is optional (defaults to `""`).

---

## Notes

- Storage is **in-memory** — data resets on restart.
- The storage layer is isolated; a real database can replace it without touching routes/controllers.
- Timestamps are ISO-8601 UTC strings.
