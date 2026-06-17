from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from . import queue
from .database import get_db
from .models import Transaction
from .schemas import ScoreResult, TransactionIn

router = APIRouter()


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
    db.commit()

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
    transaction_id: str, payload: ScoreResult, db: Session = Depends(get_db)
):
    txn = db.get(Transaction, transaction_id)
    if txn is None:
        return JSONResponse(status_code=404, content={"error": "not found"})

    txn.score = payload.score
    txn.risk_level = payload.risk_level
    txn.status = "scored"
    db.add(txn)
    db.commit()

    return {"ok": True}
