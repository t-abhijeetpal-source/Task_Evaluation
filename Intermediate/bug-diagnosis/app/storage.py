"""In-memory order storage."""

from typing import Dict, List

from app.schemas import Item


class OrderStore:
    def __init__(self) -> None:
        self._orders: Dict[int, List[Item]] = {}
        self._next_id = 1

    def add(self, items: List[Item]) -> int:
        order_id = self._next_id
        self._next_id += 1
        self._orders[order_id] = items
        return order_id

    def get(self, order_id: int):
        return self._orders.get(order_id)

    def clear(self) -> None:
        self._orders.clear()
        self._next_id = 1


store = OrderStore()
