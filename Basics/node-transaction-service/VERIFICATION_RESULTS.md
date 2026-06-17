# B5 — Verification Run Results (Node.js transaction service)

> B5 is a **greenfield builder** (Node.js/Express service from scratch), not a repo-reader — so it
> is verified by building + running its own tests, not by analyzing an existing repo.
> Re-validated 2026-06-17 (Node v26 · jest).

## Status: ✅ VERIFIED

```text
$ npm test
  ✓ creates a transaction and returns its id (18 ms)
  ✓ lists all transactions (4 ms)
  ✓ computes balance = sum(credits) - sum(debits) (3 ms)
  ✓ balance is 0 when there are no transactions (1 ms)
  ✓ rejects non-positive amount with 422 (2 ms)
  ✓ rejects invalid type with 422
  ✓ rejects malformed JSON with 400 (3 ms)
Test Suites: 1 passed, 1 total
Tests:       7 passed, 7 total
```

**Result: 7 passed, 0 failed.** Layered Express app (routes→controllers→service→storage),
input validation incl. malformed-JSON 400. Architecture + live curl evidence in
`docs/agent-analysis/B5_node_service.md`.

Run standalone: `cd B5 && npm install && npm test`  (server: `npm start`)
