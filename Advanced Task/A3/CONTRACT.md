# A3 — Shared Data Contract & Scoring Rules (v1.0, LOCKED)

> The single source of truth every component (FastAPI, Node worker, Rust engine) builds to.
> Components are authored in parallel against THIS contract so they integrate without conflicts.

---

## Transaction schema — `schema_version: "1.0"`

```json
{
  "schema_version": "1.0",
  "transaction_id": "txn_001",
  "user_id": "user_123",
  "amount": 5000,
  "country": "IN",
  "merchant_category": "electronics",
  "timestamp": "2026-06-17T10:00:00Z"
}
```

| Field | Type | Required | Rule / meaning |
|---|---|---|---|
| `schema_version` | string | no (default `"1.0"`) | contract version |
| `transaction_id` | string | **yes** | unique id (used as the key / queue filename) |
| `user_id` | string | **yes** | owning user |
| `amount` | number | **yes** | must be `> 0` |
| `country` | string | **yes** | ISO-2 country code; **home country = `IN`** |
| `merchant_category` | string | **yes** | free text; see high-risk set below |
| `timestamp` | string | **yes** | ISO-8601 UTC |

## Score result schema — `schema_version: "1.0"`

```json
{
  "schema_version": "1.0",
  "transaction_id": "txn_001",
  "score": 60,
  "risk_level": "medium",
  "reasons": ["high_amount", "foreign_country"]
}
```

| Field | Type | Meaning |
|---|---|---|
| `transaction_id` | string | echoes the input |
| `score` | integer | 0–100 (clamped) |
| `risk_level` | string | `low` (<30) · `medium` (30–69) · `high` (≥70) |
| `reasons` | string[] | which rules fired |

---

## Scoring rules (DETERMINISTIC — implemented ONLY in the Rust engine)

Start at `0`, add points, clamp to `[0,100]`:

| Condition | Points | Reason code |
|---|---|---|
| `amount > 10000` | +40 | `high_amount` |
| `country != "IN"` (foreign) | +20 | `foreign_country` |
| `merchant_category` ∈ HIGH-RISK set | +30 | `high_risk_merchant` |

**HIGH-RISK merchant set:** `{ "gambling", "crypto", "jewelry", "wire_transfer" }`.

`risk_level`: `score < 30 → low`, `30 ≤ score ≤ 69 → medium`, `score ≥ 70 → high`.

### Canonical test vectors (all components assert these)
| transaction | amount | country | merchant | → score | risk | reasons |
|---|---|---|---|---|---|---|
| baseline | 5000 | IN | electronics | **0** | low | [] |
| high amount | 15000 | IN | electronics | **40** | medium | [high_amount] |
| foreign | 5000 | US | electronics | **20** | low | [foreign_country] |
| all three | 15000 | US | gambling | **90** | high | [high_amount, foreign_country, high_risk_merchant] |

---

## Integration flow (file-queue + HTTP callback — no external infra)

```
Client → POST /transactions (FastAPI)
       → validate (Pydantic) + store (SQLite, status=pending) + ENQUEUE queue/<txn_id>.json
Node worker (--once or loop):
       → read queue/<txn_id>.json
       → spawn rust-engine (txn JSON on stdin) → score JSON on stdout
       → POST /internal/transactions/<id>/score  (FastAPI persists, status=scored)
       → move queue file to processed/ (or failed/ after retries)
GET /transactions/<id> (FastAPI) → returns txn + score + status
```

## Component interfaces (LOCKED)

**FastAPI** (`fastapi-service/`, port 8000):
- `POST /transactions` body=Transaction → `201 {transaction_id, status:"pending", request_id}`; `422 {"error":...}` on invalid (amount≤0, missing fields).
- `GET /transactions/{id}` → `200 {transaction, score|null, risk_level|null, status}`; `404` if unknown.
- `POST /internal/transactions/{id}/score` body=ScoreResult → `200`; persists score, status=`scored`.
- `GET /health` → `{"status":"ok"}`.
- Env: `QUEUE_DIR` (default `./queue`), `DATABASE_URL` (default sqlite file). Structured JSON logs with `request_id`.

**Rust engine** (`rust-engine/`, binary `fraud-engine`):
- Reads ONE transaction JSON from **stdin** → writes ONE score-result JSON to **stdout**, exit `0`.
- Malformed/invalid input → error JSON to **stderr**, exit `1` (no panic).
- Also a library crate exposing `score(transaction) -> ScoreResult` for unit tests.

**Node worker** (`node-worker/`):
- `node src/worker.js --once` processes the current queue and exits (used by integration test);
  default (no flag) polls in a loop.
- For each queue file: spawn `fraud-engine`, parse score, POST to FastAPI `/internal/.../score`.
- Retry the Rust call up to 3× with backoff; after failure move file to `failed/`. Structured JSON logs.
- Env: `API_URL` (default `http://localhost:8000`), `QUEUE_DIR`, `ENGINE_BIN` (path to fraud-engine).

---

## Repository layout

```
A3/
├── fastapi-service/   (app/, tests/, requirements.txt)
├── node-worker/       (src/, tests/, package.json)
├── rust-engine/       (src/, tests/, Cargo.toml)
├── integration-tests/ (end-to-end script — coordinator owns)
├── CONTRACT.md        (this file)
├── README.md
└── docs/agent-analysis/A3_polyglot_system.md
```
