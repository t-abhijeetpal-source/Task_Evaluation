# A5 — Adversarial PR Review & Remediation (Polyglot Fraud System)

Principal-engineer / red-team review of the A3 polyglot fraud-score system
(`../polyglot-fraud-system/`), **with the remediation loop closed**: every blocking defect is fixed and
re-verified by re-running the original exploit, and each fix is covered by a regression test.

**Posture:** assume every line is wrong until an exploit is reproduced or safety is proven by a test.

## Results at a glance

| | Before (audit) | After (this deliverable) |
|---|---|---|
| Blocking defects open | 8 | **0** |
| Internal `/internal/*` auth | **fail-open** (default config) | **fail-closed** (503 when unconfigured) |
| Integration E2E | **broken** — `exit 1` (unbound var) | **4/4 PASS, exit 0** |
| Score callback | accepts 999 / wrong band / overwrite / id-mismatch | validated + idempotent + 409-on-conflict |
| Concurrent duplicate create | **HTTP 500** | **409** |
| Test suites | rust 6 · pytest 10 · node 12 | rust 7 · **pytest 18** · **node 14** · e2e 4/4 |
| Findings | 12 | **20** across 8 attack categories |

## Deliverable tree

```
adversarial-pr-review/
├── README.md                                  ← this file
├── docs/
│   ├── agent-analysis/A5_adversarial_review.md ← full review (20 findings, honest v1 correction)
│   ├── REMEDIATION_LOG.md                       ← per-fix before/after + repro pointers
│   └── TEST_MATRIX.md                           ← finding → regression test mapping
└── artifacts/repro/
    ├── api_exploits_repro.py                    ← reusable live exploit harness (before/after)
    ├── BEFORE_api_exploits.txt                  ← all API exploits succeeding (vulnerable)
    ├── AFTER_api_exploits.txt                   ← same exploits rejected (token configured)
    ├── AFTER_failclosed_default_config.txt      ← default config denies /internal/* (503)
    ├── BEFORE_integration.txt                   ← harness aborts: unbound variable, exit 1
    └── suites/
        ├── AFTER_integration.txt                ← INTEGRATION: PASS (4/4), exit 0
        ├── AFTER_rust.txt  AFTER_pytest.txt  AFTER_node.txt
```

## What was fixed (in the system under test)

Code changes live in `../polyglot-fraud-system/`:
* `fastapi-service/app/routes.py` — fail-closed internal auth (constant-time), score range/band/id
  validation, idempotent + overwrite-resistant callback, `IntegrityError`→409.
* `fastapi-service/app/schemas.py` — `ScoreResult.score` bounds + `transaction_id` pattern (defense-in-depth).
* `fastapi-service/tests/` — 8 new regression tests + token fixture (10 → 18).
* `node-worker/src/worker.js` — engine timeout (A5-7) + stdout cap (A5-10); 2 new tests (12 → 14).
* `rust-engine/tests/scoring.rs` — high-amount threshold boundary test (guards deferred A5-4).
* `integration-tests/run_integration.sh` — fixed unbound `$polyglot-fraud-system` → `$A3`; shared token.

## Reproduce everything

```bash
SUT=../polyglot-fraud-system

( cd $SUT/rust-engine     && cargo test )                       # 7 passed
( cd $SUT/fastapi-service && .venv/bin/python -m pytest -q )     # 18 passed
( cd $SUT/node-worker     && npm test )                          # 14 passed
bash $SUT/integration-tests/run_integration.sh; echo "exit=$?"   # INTEGRATION: PASS, exit=0

# Live exploit harness — fail-closed default vs. authenticated:
( cd $SUT/fastapi-service && PYTHONPATH="$PWD" .venv/bin/python \
    ../../adversarial-pr-review/artifacts/repro/api_exploits_repro.py --with-token )
```

See `docs/agent-analysis/A5_adversarial_review.md` for the full finding inventory and the correction to
the overstated v1 remediation claims.
