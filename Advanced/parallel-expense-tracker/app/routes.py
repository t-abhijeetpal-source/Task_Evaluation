from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Expense
from app.schemas import ExpenseCreate, ExpenseOut, Summary

router = APIRouter(prefix="/api")


@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/expenses", status_code=201, response_model=ExpenseOut)
def create_expense(payload: ExpenseCreate, db: Session = Depends(get_db)):
    if payload.amount <= 0:
        return JSONResponse(
            status_code=422, content={"error": "amount must be positive"}
        )

    expense = Expense(
        amount=payload.amount,
        category=payload.category,
        note=payload.note or "",
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    db.add(expense)
    db.commit()
    db.refresh(expense)
    return expense


@router.get("/expenses", response_model=list[ExpenseOut])
def list_expenses(db: Session = Depends(get_db)):
    return db.query(Expense).order_by(Expense.id.desc()).all()


@router.get("/summary", response_model=Summary)
def summary(db: Session = Depends(get_db)):
    # Aggregate in SQL (GROUP BY) instead of materializing every row as an ORM
    # object and summing in Python — the DB returns one row per category.
    rows = (
        db.query(
            Expense.category,
            func.sum(Expense.amount),
            func.count(Expense.id),
        )
        .group_by(Expense.category)
        .all()
    )
    by_category = {cat: float(cat_total) for cat, cat_total, _ in rows}
    total = float(sum(by_category.values()))
    count = sum(cat_count for _, _, cat_count in rows)
    return Summary(total=total, count=count, by_category=by_category)
