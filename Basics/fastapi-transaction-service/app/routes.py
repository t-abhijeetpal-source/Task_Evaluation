"""API layer — HTTP routing only."""

from typing import List

from fastapi import APIRouter, Depends, Query

from app.schemas import (
    BalanceResponse,
    CreateResponse,
    TransactionCreate,
    TransactionOut,
)
from app.services import TransactionService
from app.storage import InMemoryStorage, storage

router = APIRouter()


def get_store() -> InMemoryStorage:
    """Dependency provider — wires routes to the active storage instance."""
    return storage


def get_service(store: InMemoryStorage = Depends(get_store)) -> TransactionService:
    """Dependency provider — wires the service to storage."""
    return TransactionService(store)


@router.post("/transactions", response_model=CreateResponse, status_code=201)
def create_transaction(
    payload: TransactionCreate,
    service: TransactionService = Depends(get_service),
) -> CreateResponse:
    """Create a transaction. Returns the new id."""
    txn = service.create_transaction(payload)
    return CreateResponse(id=txn.id)


@router.get("/transactions", response_model=List[TransactionOut])
def list_transactions(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    service: TransactionService = Depends(get_service),
) -> List[TransactionOut]:
    """List transactions with optional pagination."""
    return service.list_transactions(limit=limit, offset=offset)


@router.get("/balance", response_model=BalanceResponse)
def get_balance(
    service: TransactionService = Depends(get_service),
) -> BalanceResponse:
    """Return the current balance = sum(credits) - sum(debits)."""
    return BalanceResponse(balance=service.get_balance())
