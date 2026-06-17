# A3 — Polyglot Fraud-Score System

A distributed fraud-scoring system across **three languages**, integrated end-to-end:

```
Client → FastAPI (Python, ingest+enqueue) → queue/ → Node worker → Rust engine (score) → POST back → GET shows score
```

- **`fastapi-service/`** — Python/FastAPI: validate + store + enqueue transactions; serve results.
- **`node-worker/`** — Node.js: consume the queue, invoke the Rust engine, post the score back (with retries).
- **`rust-engine/`** — Rust: deterministic risk scoring (CLI + library).
- **`integration-tests/`** — end-to-end test running all three real components.
- **`CONTRACT.md`** — the shared, versioned data contract + scoring rules (single source of truth).

## Status

✅ Verified: Rust `cargo test` **6 passed**, FastAPI `pytest` **7 passed**, Node `npm test` **12 passed**,
end-to-end integration **4/4 PASS**. See `docs/agent-analysis/A3_polyglot_system.md` for full evidence + diagrams.

## Run it locally

```bash
# 1. Rust engine (build the binary the worker calls)
cd rust-engine && cargo build --release && cargo test

# 2. FastAPI service
cd ../fastapi-service && python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && pytest -q
uvicorn app.main:app --port 8000        # leave running

# 3. Node worker (new terminal)
cd ../node-worker && npm install && npm test
QUEUE_DIR=../fastapi-service/queue API_URL=http://localhost:8000 \
  ENGINE_BIN=../rust-engine/target/release/fraud-engine \
  node src/worker.js            # polls the queue; or add --once

# 4. Try it
curl -X POST localhost:8000/transactions -H 'Content-Type: application/json' \
  -d '{"transaction_id":"txn_all","user_id":"u1","amount":15000,"country":"US","merchant_category":"gambling","timestamp":"2026-06-17T10:00:00Z"}'
curl localhost:8000/transactions/txn_all   # -> score 90, risk high (after the worker runs)
```

## One-command end-to-end test

```bash
bash integration-tests/run_integration.sh   # starts API, posts 4 txns, runs worker, asserts scores
```

## Scoring rules (deterministic, in Rust)

`amount > 10000` → +40 · foreign (`country != IN`) → +20 · high-risk merchant
(`gambling/crypto/jewelry/wire_transfer`) → +30 · clamp 0–100 · `low<30 / medium 30–69 / high≥70`.

See `CONTRACT.md` for the full schema and `docs/agent-analysis/A3_polyglot_system.md` for architecture,
failure modes, and verification evidence.
