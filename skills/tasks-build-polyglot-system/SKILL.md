---
name: tasks-build-polyglot-system
description: >-
  Builds a three-language distributed system (FastAPI + Node worker + Rust engine) with shared
  contract and integration tests. Use when the user asks for polyglot system, fraud scoring,
  multi-language integration, or A3-style build.
---

# Build Polyglot System Agent

> A reusable agent spec for a **three-language distributed system** — FastAPI ingest + Node worker +
> Rust scoring engine — built against a locked `CONTRACT.md` so the components integrate without
> conflict, proven by an end-to-end integration run.
> Goal: all three component suites + the e2e integration green, in **under 3 hours**.

## Role

You are a **Principal Polyglot Architect** building a distributed system across Python (FastAPI), Node.js (worker), and Rust (engine) with a **locked shared contract** so components integrate without conflicts.

## Mission

Deliver three independently testable components plus end-to-end integration tests — all aligned to `CONTRACT.md`.

## Architecture

```
Client → FastAPI (ingest + enqueue) → file queue → Node worker → Rust engine (score) → POST back → GET shows score
```

## Components

| Component | Language | Responsibility |
|---|---|---|
| `fastapi-service/` | Python | Validate + store + enqueue transactions; serve results |
| `node-worker/` | Node.js | Consume queue, invoke Rust engine, post score back (retries) |
| `rust-engine/` | Rust | Deterministic risk scoring (CLI + library) |
| `integration-tests/` | Shell/pytest | End-to-end test running all three real components |
| `CONTRACT.md` | — | Shared data contract + scoring rules (single source of truth) |

## Phase 1 — Lock CONTRACT.md

Define before parallel build:

- **Transaction schema** — fields, types, validation rules (`transaction_id`, `amount > 0`, etc.).
- **Score result schema** — `score` 0–100, `risk_level`, `reasons[]`.
- **Scoring rules** — deterministic, implemented ONLY in Rust engine.
- **Integration flow** — file-queue + HTTP callback (no external infra).
- **Canonical test vectors** — all components must assert same inputs → same scores.

## Scoring Rules (reference)

Start at 0, add points, clamp [0,100]:

| Condition | Points | Reason code |
|---|---|---|
| `amount > 10000` | +40 | `high_amount` |
| `country != "IN"` | +20 | `foreign_country` |
| high-risk merchant | +30 | `high_risk_merchant` |

Risk levels: `low < 30`, `medium 30–69`, `high ≥ 70`.

## Phase 2 — Parallel Build

Each component built against CONTRACT.md. Scoring logic lives **only** in Rust.

## Phase 3 — Security Hardening (post-build)

- Validate `transaction_id` with strict allowlist (prevent path traversal in queue filenames).
- Authenticate `/internal/*` endpoints with shared secret header.
- Idempotent create → 409 on duplicate ID (not 500).

## Verification

```bash
cd rust-engine && cargo test
cd fastapi-service && pytest -q
cd node-worker && npm test
bash integration-tests/run_integration.sh   # 4/4 PASS
```

Paste all outputs. Live demo: POST transaction, worker processes, GET shows score.

## Deliverables

- `CONTRACT.md`, three components, `integration-tests/`, `docs/agent-analysis/A3_polyglot_system.md`

## Final Output

- Per-component test counts, integration result, contract path, architecture doc path.
