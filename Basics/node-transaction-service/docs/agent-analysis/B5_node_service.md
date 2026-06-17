# B5 — Node.js Transaction Tracker Service

> Build report for the Node.js / Express transaction tracking API.
> Status: **BUILT, TESTED, AND VERIFIED RUNNING.**
> Node v25.9.0 · Express 4 · Jest 29 · supertest 7.

---

## Architecture

Four strictly separated layers, dependencies pointing inward:

```text
HTTP request
   │
   ▼
Routes        src/routes/transactions.js          path -> controller
   │          src/app.js / src/server.js          app factory + entry point
   ▼
Controllers   src/controllers/transactionController.js   HTTP <-> service, status codes
   │
   ▼
Service       src/services/transactionService.js   validation + create/list/balance
   │
   ▼
Storage       src/storage/inMemoryStorage.js       in-memory store (swappable)

Domain model: src/models/transaction.js            valid types + factory
```

- **No business logic in controllers** — they validate via the service and map results to status codes.
- **App factory pattern** — `createApp()` returns the Express app without listening, so tests
  import it directly with supertest (no real port needed).

---

## Request Flow

`POST /transactions`:
```
client
  → express.json() parses body         (malformed JSON -> 400 via error middleware)
  → router matches POST /transactions
  → controller.createTransaction
      → service.validate(body)         (-> 422 with {errors:[...]} if invalid)
      → service.create(body)           (model factory -> storage.add assigns id)
  → 201 { "id": <n> }
```

`GET /balance` → controller → `service.getBalance()` → `reduce` over store
(`credit` adds, `debit` subtracts) → `200 { "balance": <n> }`.

---

## Validation

Performed in `TransactionService.validate()` (business layer), returning an array of messages:

| Condition | Result |
|---|---|
| body not a JSON object | `422` |
| `amount` missing / NaN / not a number | `422` |
| `amount <= 0` | `422` |
| `type` not in `['credit','debit']` | `422` |
| `description` present but not a string | `422` |
| Malformed JSON (parser failure) | `400` (handled in `app.js` error middleware) |

Valid `description` is optional and defaults to `""`.

---

## Testing

**Commands:** `npm install` then `npm test` (`jest --runInBand`).

```text
> jest --runInBand

PASS tests/transactions.test.js
  Transaction Tracker API
    ✓ creates a transaction and returns its id (23 ms)
    ✓ lists all transactions (5 ms)
    ✓ computes balance = sum(credits) - sum(debits) (4 ms)
    ✓ balance is 0 when there are no transactions (1 ms)
    ✓ rejects non-positive amount with 422 (2 ms)
    ✓ rejects invalid type with 422 (1 ms)
    ✓ rejects malformed JSON with 400 (2 ms)

Test Suites: 1 passed, 1 total
Tests:       7 passed, 7 total
Time:        0.44 s
```

**Pass/fail count: 7 passed, 0 failed.** Covers all 4 required tests
(creation, listing, balance, validation failure) plus empty-balance and malformed-JSON bonuses.

### Live server verification

Server started with `PORT=3099 node src/server.js`, then:

```text
GET  /health                       -> {"status":"ok"}
POST /transactions (credit 100)    -> {"id":1}
POST /transactions (debit 40)      -> {"id":2}
GET  /transactions                 -> [ {id:1,amount:100,type:credit,...},
                                        {id:2,amount:40,type:debit,...} ]
GET  /balance                      -> {"balance":60}     (100 - 40 = 60 ✓)
POST amount:0                      -> HTTP 422
POST type:"transfer"               -> HTTP 422
POST malformed JSON                -> HTTP 400
```

---

## Commands

```bash
cd B5
npm install        # install express, jest, supertest
npm start          # run server on :3000 (PORT to override)
npm test           # run jest suite
```

---

## Known Limitations

- **In-memory storage** — data lost on restart; not shared across processes/cluster workers.
- **No persistence/migrations** — a real DB would replace `storage/inMemoryStorage.js`.
- **No authentication/authorization** — all endpoints public.
- **No pagination** on `GET /transactions`.
- **Number amounts** — fine here; production money handling should avoid float rounding.
- **npm audit** reported moderate advisories in the transitive dev dependency tree (jest/supertest);
  not addressed as they don't affect runtime and are out of scope for this exercise.

---

## Provenance

| Item | Status |
|---|---|
| Application code (`src/`) | **NOT VERIFIED (agent generated)** |
| Tests (`tests/`) | **NOT VERIFIED (agent generated)** |
| README | **NOT VERIFIED (agent generated)** |
| `npm install` (355 packages added) | **VERIFIED** — command executed |
| `npm test` (7 passed) | **VERIFIED** — command executed, output captured above |
| Live curl responses + balance math + 400/422 | **VERIFIED** — server run, endpoints called |
