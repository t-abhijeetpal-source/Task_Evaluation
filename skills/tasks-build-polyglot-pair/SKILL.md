---
name: tasks-build-polyglot-pair
description: >-
  Builds a two-component polyglot system (FastAPI service + Node.js CLI client) with integration
  tests. Use when the user asks for polyglot pair, FastAPI + Node client, currency converter, or I4-style build.
---

# Build Polyglot Pair Agent

> A reusable agent spec for a **two-component polyglot system** — a FastAPI HTTP service and a Node.js
> CLI client over REST — each independently tested, plus a verified live HTTP integration between them.
> Goal: both suites green + a live CLI→service round-trip, in **under 90 minutes**.

## Role

You are a **Full-Stack Polyglot Engineer** building a two-component system: a Python FastAPI HTTP service and a Node.js CLI client that communicates over REST.

## Mission

Deliver both components runnable from a fresh clone, each with its own test suite, plus verified HTTP integration between them.

## Architecture

```mermaid
flowchart LR
    User([User]) --> CLI[Node.js CLI]
    CLI -->|POST JSON over HTTP| API[FastAPI Service]
    API --> Service[Business Logic]
    Service --> CLI
```

## Target Structure

```text
fastapi-service/
├── app/
│   ├── main.py        # app bootstrap + /health
│   ├── routes.py      # HTTP boundary only
│   ├── schemas.py     # Pydantic validation
│   └── services.py    # business logic + hardcoded rates/data
├── tests/test_*.py
├── requirements.txt
└── README.md
node-client/
├── src/convert.js     # CLI: parse args → HTTP call → format output
├── tests/convert.test.js
├── package.json
└── README.md
README.md              # top-level setup + verification
docs/agent-analysis/I4_polyglot_service.md
```

## Workflow

1. **Design API contract** — define request/response JSON (e.g. `POST /convert` with `{amount, from_currency, to_currency}`).
2. **FastAPI service** — layered app; typed errors → 200/400/422; `/health` endpoint.
3. **Service tests** — pytest with TestClient; cover valid conversion, unsupported currency, validation.
4. **Node CLI** — parse CLI args, POST to service, format human-readable output; `API_URL` env override.
5. **CLI tests** — jest with mocked HTTP or test fixtures.
6. **Integration verify** — start service, run CLI against live API, capture output.
7. **Document** — setup for both terminals, verification steps, architecture diagram.

## Error Handling Contract

| Case | HTTP status |
|---|---|
| Valid request | `200` |
| Unsupported currency pair | `400` with message |
| Invalid payload | `422` |

## Verification Rules

- Run `pytest -v` in fastapi-service — paste output.
- Run `npm test` in node-client — paste output.
- Live integration: start uvicorn, run CLI, show formatted result.
- CLI defaults to `http://localhost:8000`; document `API_URL` override.
- If a fact can't be confirmed from the repo, write exactly: `NOT FOUND IN REPOSITORY` — never fabricate.

## Efficiency & Safety Guidance (advanced)

- **Pin the JSON contract first** — request/response shape and status codes are the seam both
  components build against; lock it before either side starts.
- **Share business primitives, don't duplicate them** — if both sides need the same money/decimal
  rules, extract a tiny shared core rather than re-implementing (the I4 reference uses a
  `currency_core` with Decimal to avoid float drift across languages).
- **Test each side in isolation, then prove the wire** — unit-test the service with TestClient and the
  CLI with mocked HTTP; the live integration run is what proves they actually agree over the network.
- **`API_URL` override** keeps the CLI portable — never hardcode the host beyond a sane default.
- The integration step is the real proof: start the service, run the CLI against it, paste the output.

## Reference implementation in this repo

- **`Intermediate/polyglot-currency-pair/`** — FastAPI service + Node CLI sharing a `currency_core`
  (Decimal), string-amount CLI, pinned Python 3.12.7 / Node 22.11.0.
- **`make i4-verify`** (repo root) — service pytest + client jest + live integration + a perf gate.

## Final Output

- Both component paths, test results, integration command + output, artifact path.
