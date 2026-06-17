# I4 — Verification Run Results

> Captured output from actually running the I4 system. Every line below is real, executed output.
> Environment: macOS (Darwin 25.5.0) · Python 3.14.6 · Node v26.3.0 · pytest 8.4.2 · jest 29.

---

## 1. Service tests — `pytest`

```text
$ cd fastapi-service && source .venv/bin/activate && python -m pytest -q
.......                                                                  [100%]
7 passed, 1 warning in 0.26s
```
**Result: 7 passed, 0 failed — 0.26s.**
(The 1 warning is a Starlette `TestClient`/httpx deprecation notice; not a failure.)

---

## 2. Client tests — `npm test`

```text
$ cd node-client && npm test
PASS tests/convert.test.js
Test Suites: 1 passed, 1 total
Tests:       9 passed, 9 total
Time:        0.296 s
```
**Result: 9 passed, 0 failed — 0.30s.**

---

## 3. Live integration (real HTTP)

### Performance
```text
server cold-start:           0.56s
POST /convert latency:       HTTP 200 in 0.001692s  (~1.7 ms)
```

### Curl
```text
$ curl -X POST localhost:8000/convert -d '{"amount":100,"from":"USD","to":"INR"}'
HTTP 200  in 0.001692s
{"converted_amount":8300,"from":"USD","to":"INR"}
```

### All 6 conversion rate pairs (Node CLI → live FastAPI)
```text
100 USD INR    -> 100 USD = 8300 INR     (×83)
100 USD EUR    -> 100 USD = 92 EUR       (×0.92)
100 INR USD    -> 100 INR = 1.2 USD      (×0.012)
100 EUR USD    -> 100 EUR = 108 USD      (×1.08)
100 INR EUR    -> 100 INR = 1.1 EUR      (×0.011)
100 EUR INR    -> 100 EUR = 9000 INR     (×90)
```
All six match the hardcoded rates exactly.

### Error paths (exit codes)
```text
$ node src/convert.js 100 USD GBP   -> Error: Unsupported currency                              (exit 1)
$ node src/convert.js -5 USD INR    -> Error: Amount must be positive                           (exit 2)
$ node src/convert.js 100 USD       -> Error: Usage: node convert.js <amount> <from> <to> ...   (exit 2)
$ node src/convert.js 100 USD INR   -> Error: API unavailable at http://localhost:8000 ...      (exit 3)   [server stopped]
```

---

## Summary

| Check | Command | Result | Time |
|---|---|---|---|
| Service tests | `pytest -q` | 7 passed | 0.26s |
| Client tests | `npm test` | 9 passed | 0.30s |
| Server cold-start | `uvicorn ...` | ready | 0.56s |
| Request latency | `curl POST /convert` | HTTP 200 | ~1.7ms |
| All 6 rate pairs | live CLI | correct | — |
| Error paths (1/2/3) | live CLI | correct exit codes | — |

**Verdict: I4 works end-to-end, correctly and efficiently.**

---

## Note — one harness artifact (not a code bug)

A first attempt to loop the 6 pairs printed a `Usage:` error for every pair. Cause: a **zsh
quirk** — unlike bash, zsh does not word-split an unquoted `$pair`, so `"100 USD INR"` was passed
as a single argument. Re-running with zsh explicit split (`${=pair}`) produced the correct output
shown above. The application behaved correctly throughout; this was purely a shell-quoting
artifact in the test command.
