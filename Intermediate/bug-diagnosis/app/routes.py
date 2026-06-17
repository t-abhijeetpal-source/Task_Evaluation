"""API layer — HTTP routing only."""

from fastapi import APIRouter, HTTPException

from app import services
from app.schemas import OrderCreate, OrderCreated, OrderTotal
from app.storage import store

router = APIRouter()


@router.post("/orders", response_model=OrderCreated, status_code=201)
def create_order(payload: OrderCreate) -> OrderCreated:
    order_id = store.add(payload.items)
    return OrderCreated(id=order_id)


@router.get("/orders/{order_id}/total", response_model=OrderTotal)
def get_order_total(order_id: int) -> OrderTotal:
    items = store.get(order_id)
    if items is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return OrderTotal(id=order_id, total=services.calculate_total(items))
