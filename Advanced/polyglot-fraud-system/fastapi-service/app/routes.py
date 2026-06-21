import hmac
import os
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from . import queue
from .database import get_db
from .models import Transaction
from .schemas import ScoreResult, TransactionIn

router = APIRouter()

# Shared-secret for the internal scoring callback (A5-2 / A5-17).
#
# FAIL-CLOSED: the /internal/* callback is a privileged surface — anyone who can
# reach it can overwrite fraud scores. We therefore require A3_INTERNAL_TOKEN to
# be configured in EVERY environment. When it is unset (or empty) the endpoint
# denies all callers (503 misconfigured) rather than silently accepting them.
# There is no configuration in which /internal/* is reachable without a token.
_INTERNAL_TOKEN = os.environ.get("A3_INTERNAL_TOKEN") or None

_VALID_RISK_LEVELS = {"low", "medium", "high"}


def _risk_band(score: int) -> str:
    """Risk level for a score, per CONTRACT.md (<30 low, 30-69 medium, >=70 high)."""
    if score < 30:
        return "low"
    if score <= 69:
        return "medium"
    return "high"


def _check_internal_auth(token: str | None) -> JSONResponse | None:
    """Return a JSONResponse to short-circuit with, or None when authorized.

    Fail-closed: deny when no server-side token is configured, and use a
    constant-time comparison to avoid leaking the token via timing (A5-19).
    """
    if not _INTERNAL_TOKEN:
        return JSONResponse(
            status_code=503,
            content={"error": "internal auth not configured"},
        )
    if token is None or not hmac.compare_digest(token, _INTERNAL_TOKEN):
        return JSONResponse(status_code=401, content={"error": "unauthorized"})
    return None


def _txn_to_dict(txn: Transaction) -> dict:
    return {
        "schema_version": "1.0",
        "transaction_id": txn.transaction_id,
        "user_id": txn.user_id,
        "amount": txn.amount,
        "country": txn.country,
        "merchant_category": txn.merchant_category,
        "timestamp": txn.timestamp,
    }


@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/transactions")
def create_transaction(
    payload: TransactionIn, request: Request, db: Session = Depends(get_db)
):
    if payload.amount <= 0:
        return JSONResponse(
            status_code=422, content={"error": "amount must be positive"}
        )

    request_id = getattr(request.state, "request_id", None)

    # Idempotency: a duplicate transaction_id must not crash with a 500 (A5-3).
    if db.get(Transaction, payload.transaction_id) is not None:
        return JSONResponse(
            status_code=409,
            content={"error": "transaction_id already exists", "transaction_id": payload.transaction_id},
        )

    txn = Transaction(
        transaction_id=payload.transaction_id,
        user_id=payload.user_id,
        amount=payload.amount,
        country=payload.country,
        merchant_category=payload.merchant_category,
        timestamp=payload.timestamp,
        status="pending",
        score=None,
        risk_level=None,
        request_id=request_id,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    db.add(txn)
    try:
        db.commit()
    except IntegrityError:
        # A5-16: the db.get() pre-check above is a TOCTOU window — two concurrent
        # creates with the same id both see "not found" and race to INSERT. The
        # PK uniqueness constraint is the real guard; translate the loser's
        # violation into the same idempotent 409 instead of an unhandled 500.
        db.rollback()
        return JSONResponse(
            status_code=409,
            content={
                "error": "transaction_id already exists",
                "transaction_id": payload.transaction_id,
            },
        )

    queue.enqueue(
        {
            "schema_version": payload.schema_version,
            "transaction_id": payload.transaction_id,
            "user_id": payload.user_id,
            "amount": payload.amount,
            "country": payload.country,
            "merchant_category": payload.merchant_category,
            "timestamp": payload.timestamp,
        }
    )

    return JSONResponse(
        status_code=201,
        content={
            "transaction_id": payload.transaction_id,
            "status": "pending",
            "request_id": request_id,
        },
    )


@router.get("/transactions/{transaction_id}")
def get_transaction(transaction_id: str, db: Session = Depends(get_db)):
    txn = db.get(Transaction, transaction_id)
    if txn is None:
        return JSONResponse(status_code=404, content={"error": "not found"})

    return {
        "transaction": _txn_to_dict(txn),
        "score": txn.score,
        "risk_level": txn.risk_level,
        "status": txn.status,
    }


@router.post("/internal/transactions/{transaction_id}/score")
def score_transaction(
    transaction_id: str,
    payload: ScoreResult,
    db: Session = Depends(get_db),
    x_internal_token: str | None = Header(default=None),
):
    # 1) Fail-closed auth on the privileged callback (A5-2 / A5-17 / A5-19).
    denied = _check_internal_auth(x_internal_token)
    if denied is not None:
        return denied

    # 2) Path/body id must agree — a mismatch is a confused-deputy bug that
    #    would let one transaction's score be written under another id (A5-15).
    if payload.transaction_id != transaction_id:
        return JSONResponse(
            status_code=422,
            content={"error": "transaction_id in body does not match path"},
        )

    # 3) Server-side score validation (A5-13). The score itself is computed only
    #    by the Rust engine, but the server still refuses physically impossible
    #    or self-inconsistent results so a buggy/compromised worker cannot poison
    #    the store with out-of-range scores or a band that contradicts the score.
    if not (0 <= payload.score <= 100):
        return JSONResponse(
            status_code=422,
            content={"error": "score must be in [0, 100]"},
        )
    if payload.risk_level not in _VALID_RISK_LEVELS:
        return JSONResponse(
            status_code=422,
            content={"error": "risk_level must be one of low|medium|high"},
        )
    if payload.risk_level != _risk_band(payload.score):
        return JSONResponse(
            status_code=422,
            content={
                "error": "risk_level inconsistent with score",
                "expected": _risk_band(payload.score),
            },
        )

    txn = db.get(Transaction, transaction_id)
    if txn is None:
        return JSONResponse(status_code=404, content={"error": "not found"})

    # 4) Idempotent, overwrite-resistant callback (A5-14). Once a transaction is
    #    scored, an identical replay is a no-op (200) but a DIFFERENT score is a
    #    conflict (409) — an attacker (or a double-processing worker) cannot flip
    #    an already-decided high-risk score back to low.
    if txn.status == "scored":
        if txn.score == payload.score and txn.risk_level == payload.risk_level:
            return {"ok": True, "idempotent": True}
        return JSONResponse(
            status_code=409,
            content={
                "error": "transaction already scored; refusing to overwrite",
                "transaction_id": transaction_id,
                "existing": {"score": txn.score, "risk_level": txn.risk_level},
            },
        )

    txn.score = payload.score
    txn.risk_level = payload.risk_level
    txn.status = "scored"
    db.add(txn)
    db.commit()

    return {"ok": True}
