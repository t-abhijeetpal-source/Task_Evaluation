"""API layer — HTTP routing only.

Routes translate HTTP <-> service calls. They contain NO business logic:
every endpoint delegates to TransactionService. Input validation is handled
declaratively by the Pydantic schemas in the function signatures.
"""

from typing import List

from fastapi import APIRouter, Depends

from app.schemas import (
    BalanceResponse,
    CreateResponse,
    TransactionCreate,
    TransactionOut,
)
from app.services import TransactionService
from app.storage import storage

router = APIRouter()


def get_service() -> TransactionService:
    """Dependency provider — wires the service to the singleton store."""
    return TransactionService(storage)


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
    service: TransactionService = Depends(get_service),
) -> List[TransactionOut]:
    """List all transactions."""
    return service.list_transactions()


@router.get("/balance", response_model=BalanceResponse)
def get_balance(
    service: TransactionService = Depends(get_service),
) -> BalanceResponse:
    """Return the current balance = sum(credits) - sum(debits)."""
    return BalanceResponse(balance=service.get_balance())
