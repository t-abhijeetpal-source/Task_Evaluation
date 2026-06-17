# A3 — Polyglot Fraud-Score System

> A distributed fraud-scoring system across **three languages**: FastAPI (Python) ingestion +
> Node.js worker + Rust scoring engine, integrated via a file queue + HTTP callback.
> Built by 3 parallel component agents against a locked contract (`CONTRACT.md`); integrated, run,
> and **verified end-to-end** by the coordinator. Date: 2026-06-17.
> Toolchains: Python 3.14 · Node v26 · Rust 1.96.

---

## Architecture

```mermaid
flowchart LR
    Client([Client]) -->|POST /transactions| API["FastAPI Ingestion<br/>(Python) :8000"]
    API -->|enqueue JSON| Q[("queue/&lt;id&gt;.json")]
    API --> DB[("SQLite<br/>transactions")]
    Worker["Node.js Worker"] -->|read| Q
    Worker -->|spawn stdin/stdout| Engine["Rust Engine<br/>fraud-engine (CLI)"]
    Engine -->|score JSON| Worker
    Worker -->|POST /internal/.../score| API
    Client -->|GET /transactions/id| API
```

- **Component isolation:** three independently deployable units, three languages, one shared JSON
  contract. The Rust engine is the **single source of truth** for scoring; FastAPI and Node orchestrate.
- **Integration:** file queue (no external broker) + HTTP callback to persist the score.

## Sequence Diagram

```mermaid
sequenceDiagram
    actor Client
    participant API as FastAPI
    participant Q as queue/ (file)
    participant W as Node Worker
    participant R as Rust Engine
    Client->>API: POST /transactions (txn)
    API->>API: validate (Pydantic, amount>0) + assign request_id
    API->>Q: write queue/<id>.json (status=pending)
    API-->>Client: 201 {transaction_id, status:pending}
    W->>Q: read <id>.json (--once / poll)
    W->>R: spawn fraud-engine, txn JSON on stdin
    R->>R: deterministic score (rules)
    R-->>W: score JSON on stdout (exit 0)
    W->>API: POST /internal/transactions/<id>/score
    API->>API: persist score, status=scored
    Client->>API: GET /transactions/<id>
    API-->>Client: {transaction, score, risk_level, status:scored}
```

## Component Dependency Diagram

```mermaid
graph TD
    CONTRACT["CONTRACT.md (schema + rules)"]
    CONTRACT -.-> API[FastAPI service]
    CONTRACT -.-> W[Node worker]
    CONTRACT -.-> R[Rust engine]
    W -->|spawns binary| R
    W -->|HTTP callback| API
    API -->|file queue| W
    IT[integration-tests] --> API
    IT --> W
    IT --> R
```

## Data Flow Diagram

```mermaid
flowchart TD
    A[Transaction JSON v1.0] --> B{FastAPI validate}
    B -->|invalid| E[422 error]
    B -->|valid| C[(SQLite: status=pending)]
    C --> D[queue/&lt;id&gt;.json]
    D --> F[Node worker reads]
    F --> G[Rust engine scores]
    G --> H[Score result JSON v1.0]
    H --> I[POST score -> SQLite: status=scored]
    I --> J[GET /transactions/id -> score]
```

---

## Data Contracts

Versioned (`schema_version: "1.0"`), defined once in `CONTRACT.md`, used by all three components.

**Transaction:** `transaction_id, user_id, amount(>0), country(home=IN), merchant_category, timestamp(ISO-8601)`.
**Score result:** `transaction_id, score(0–100), risk_level(low/medium/high), reasons[]`.
(Full field tables in `CONTRACT.md`.)

## Scoring Rules (deterministic — Rust engine only)

| Condition | Points | Reason |
|---|---|---|
| `amount > 10000` | +40 | `high_amount` |
| `country != "IN"` | +20 | `foreign_country` |
| `merchant_category ∈ {gambling, crypto, jewelry, wire_transfer}` | +30 | `high_risk_merchant` |

Clamp `[0,100]`; `risk_level`: `<30 low · 30–69 medium · ≥70 high`.

## Failure Modes & Handling

| Failure | Component | Handling |
|---|---|---|
| Invalid request (amount≤0, missing field) | FastAPI | `422 {"error":...}` / Pydantic validation; never enqueued |
| Malformed transaction JSON in queue | Worker | caught; file moved to `failed/`; no crash |
| Rust engine error / non-zero exit | Worker | **retry up to 3×** with backoff; then move to `failed/` |
| Malformed engine stdout | Worker | reject + handled (test-covered), no crash |
| Engine bad input | Rust | error JSON to stderr, exit 1, **no panic** |
| API unreachable on callback | Worker | POST fails → logged; file not marked processed (re-attempted) |
| Unknown transaction id | FastAPI | `404` on GET and on score callback |

## Testing Strategy

- **Rust (`cargo test`):** 6 — 4 canonical vectors + clamp + malformed-input (Err, no panic).
- **FastAPI (`pytest`):** 7 — health, valid POST + queue-file written, amount≤0 → 422, missing field → 422, GET 404, score callback persists + status=scored.
- **Node (`jest`):** 12 — engine spawn success/retry/failure, postScore URL+body, processFile happy/malformed paths, queue summary (fully mocked — no real engine/API).
- **Integration (`integration-tests/run_integration.sh`):** real FastAPI + real worker + real Rust binary; 4 canonical transactions end-to-end; asserts persisted score/risk/status.

---

## Integration Results (VERIFIED — executed)

```text
# Rust
$ cargo test            -> 6 passed
$ echo '{...15000/US/gambling...}' | ./target/release/fraud-engine
   {"schema_version":"1.0","transaction_id":"t1","score":90,"risk_level":"high",
    "reasons":["high_amount","foreign_country","high_risk_merchant"]}

# FastAPI
$ pytest -q             -> 7 passed

# Node
$ npm test              -> 12 passed

# End-to-end (integration-tests/run_integration.sh)
queued files: 4
  txn_base     score=0  risk=low     status=scored  expect=0/low      PASS
  txn_high     score=40 risk=medium  status=scored  expect=40/medium  PASS
  txn_foreign  score=20 risk=low     status=scored  expect=20/low     PASS
  txn_all      score=90 risk=high    status=scored  expect=90/high    PASS
INTEGRATION: PASS   (exit 0)
```

### Sample request / response
```text
$ curl -X POST localhost:8000/transactions -d '{"transaction_id":"txn_all","user_id":"u1",
    "amount":15000,"country":"US","merchant_category":"gambling","timestamp":"2026-06-17T10:00:00Z"}'
  -> 201 {"transaction_id":"txn_all","status":"pending","request_id":"<uuid>"}
# (worker runs) then:
$ curl localhost:8000/transactions/txn_all
  -> {"transaction":{...},"score":90,"risk_level":"high","status":"scored"}
```

## Known Limitations

- **File queue, single node:** simple + infra-free, but not multi-consumer/HA. A real broker
  (Redis/SQS/Kafka) would replace `queue/` for scale and at-least-once delivery guarantees.
- **No auth** on the API (incl. the `/internal` callback) — fine for the demo; lock down for prod.
- **SQLite** single-writer; swap for Postgres at scale.
- **Worker callback is best-effort** — if the API is down at callback time the score isn't persisted
  (file remains for re-processing); no dead-letter alerting.
- **Scoring rules are fixed** in code; a real system would externalize them (rules engine/config).

---

# AGENT GENERATED
- FastAPI service (`fastapi-service/`), Node worker (`node-worker/`), Rust engine (`rust-engine/`),
  authored in parallel by 3 component agents against `CONTRACT.md`.
- Per-component tests; the shared contract; this document + README.

# VERIFIED RESULTS (coordinator-executed, evidence above)
- `cargo test` 6 passed · binary smoke test correct.
- `pytest` 7 passed.
- `npm test` 12 passed.
- **End-to-end integration: 4/4 PASS** (real cross-language flow; scores match contract).

---

## Deliverables Checklist
- [x] FastAPI Service
- [x] Node Worker
- [x] Rust Engine
- [x] Shared Contract (`CONTRACT.md`)
- [x] Tests (Rust 6 · FastAPI 7 · Node 12)
- [x] Integration Test (`integration-tests/run_integration.sh` — 4/4 PASS)
- [x] Architecture Diagrams (architecture, sequence, component-dependency, data-flow)
- [x] README
- [x] Verification Evidence (commands + outputs captured)
- [x] A3_polyglot_system.md (this file)
