"""Pydantic schemas for the orders service."""

from typing import List

from pydantic import BaseModel, Field


class Item(BaseModel):
    price: float = Field(..., gt=0, description="Unit price, must be > 0")
    qty: int = Field(..., ge=1, description="Quantity, integer >= 1")


class OrderCreate(BaseModel):
    items: List[Item] = Field(..., min_length=1)


class OrderCreated(BaseModel):
    id: int


class OrderTotal(BaseModel):
    id: int
    total: float
