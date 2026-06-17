# FastAPI Currency Conversion Service (I4)

Exposes `POST /convert` with hardcoded rates. Clean separation: route → service → validation.

## Installation

```bash
cd fastapi-service
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
uvicorn app.main:app --port 8000          # http://localhost:8000/docs
```

## Test

```bash
pytest -v
```

## API Contract

### POST /convert

**Request**
```json
{ "amount": 100, "from": "USD", "to": "INR" }
```

**Success — 200**
```json
{ "converted_amount": 8300, "from": "USD", "to": "INR" }
```

**Errors**

| Case | Status | Body |
|---|---|---|
| Unsupported currency | `400` | `{"error": "Unsupported currency"}` |
| Non-positive amount | `422` | `{"error": "Amount must be positive"}` |
| Malformed request (missing/non-numeric field) | `422` | FastAPI validation `{"detail": [...]}` |

## Example Requests

```bash
# valid
curl -X POST localhost:8000/convert -H 'Content-Type: application/json' \
  -d '{"amount":100,"from":"USD","to":"INR"}'
# -> {"converted_amount":8300,"from":"USD","to":"INR"}

# unsupported currency -> 400
curl -X POST localhost:8000/convert -H 'Content-Type: application/json' \
  -d '{"amount":100,"from":"USD","to":"GBP"}'

# negative amount -> 422
curl -X POST localhost:8000/convert -H 'Content-Type: application/json' \
  -d '{"amount":-5,"from":"USD","to":"INR"}'
```

## Layering

| Layer | File | Responsibility |
|---|---|---|
| Route | `app/routes.py` | HTTP only; maps service errors → status codes |
| Service | `app/services.py` | conversion logic + hardcoded rates (no HTTP) |
| Validation | `app/schemas.py` | Pydantic request schema (required/numeric/string) |
| Entry | `app/main.py` | FastAPI app + router mount |

Conversion logic is **not** in the routes.
