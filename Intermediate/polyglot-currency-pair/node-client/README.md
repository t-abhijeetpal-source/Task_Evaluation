# Node.js Currency Conversion CLI (I4)

A CLI client that calls the FastAPI `POST /convert` endpoint and prints the result.

## Install

```bash
cd node-client
npm install
```

## Usage

```bash
node src/convert.js <amount> <from> <to>

# example (FastAPI service must be running on :8000)
node src/convert.js 100 USD INR
# -> 100 USD = 8300 INR
```

Override the API location with the `API_URL` env var (default `http://localhost:8000`):

```bash
API_URL=http://localhost:9000 node src/convert.js 100 USD INR
```

## Test

```bash
npm test          # jest — unit tests with a mocked HTTP client (no server needed)
```

## Exit Codes

| Code | Meaning |
|---|---|
| `0` | success |
| `1` | server returned an error (e.g. unsupported currency) |
| `2` | invalid CLI arguments |
| `3` | API unavailable (service not running / connection refused) |

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `Error: API unavailable at http://localhost:8000` | FastAPI service not running | start it: `uvicorn app.main:app --port 8000` |
| `Error: Unsupported currency` | currency not in USD/INR/EUR | use a supported currency |
| `Error: Usage: node convert.js ...` | wrong number of arguments | pass exactly `<amount> <from> <to>` |
| `Error: Amount must be positive` | amount ≤ 0 | pass a positive amount |
| connects to wrong host/port | `API_URL` not set | export `API_URL` to point at the service |
