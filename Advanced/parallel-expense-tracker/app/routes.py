from datetime import datetime, timezone
from decimal import ROUND_HALF_UP

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Expense
from app.schemas import ExpenseCreate, ExpenseOut, Summary

router = APIRouter(prefix="/api")

# Pagination bounds for GET /api/expenses.
DEFAULT_LIMIT = 100
MAX_LIMIT = 1000


@router.get("/health")
def health(db: Session = Depends(get_db)):
    """Deep health check: confirms the process AND the database are reachable.

    A shallow 200 that ignores the DB would let an orchestrator route traffic to
    an instance whose datastore is down. We round-trip a trivial ``SELECT 1``;
    failure returns 503 so Docker/K8s health probes can act on it.
    """
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        return JSONResponse(
            status_code=503,
            content={"status": "unavailable", "detail": "database unreachable"},
        )
    return {"status": "ok"}


@router.post("/expenses", status_code=201, response_model=ExpenseOut)
def create_expense(payload: ExpenseCreate, db: Session = Depends(get_db)):
    # Pydantic has already guaranteed amount is finite, <= 2 dp, and in range.
    # Positivity is enforced here to preserve the documented error contract.
    if payload.amount <= 0:
        return JSONResponse(
            status_code=422, content={"error": "amount must be positive"}
        )

    # Exact conversion to integer cents (amount is finite, <= 2 decimal places).
    amount_cents = int(
        (payload.amount * 100).to_integral_value(rounding=ROUND_HALF_UP)
    )

    expense = Expense(
        amount_cents=amount_cents,
        category=payload.category,
        note=payload.note or "",
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense


@router.get("/expenses", response_model=list[ExpenseOut])
def list_expenses(
    db: Session = Depends(get_db),
    limit: int = Query(DEFAULT_LIMIT, ge=1, le=MAX_LIMIT),
    offset: int = Query(0, ge=0),
):
    return (
        db.query(Expense)
        .order_by(Expense.id.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )


@router.get("/summary", response_model=Summary)
def summary(db: Session = Depends(get_db)):
    # Aggregate in SQL (GROUP BY) over INTEGER cents — exact, no float drift —
    # then convert to a 2-decimal number once at the boundary.
    rows = (
        db.query(
            Expense.category,
            func.sum(Expense.amount_cents),
            func.count(Expense.id),
        )
        .group_by(Expense.category)
        .all()
    )
    by_category = {cat: cents / 100 for cat, cents, _ in rows}
    total_cents = sum(cents for _, cents, _ in rows)
    count = sum(cat_count for _, _, cat_count in rows)
    return Summary(total=total_cents / 100, count=count, by_category=by_category)
