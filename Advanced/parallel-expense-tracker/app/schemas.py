from typing import Optional

from pydantic import BaseModel, ConfigDict


class ExpenseCreate(BaseModel):
    amount: float
    category: str
    note: Optional[str] = ""


class ExpenseOut(BaseModel):
    id: int
    amount: float
    category: str
    note: Optional[str] = ""
    created_at: str

    model_config = ConfigDict(from_attributes=True)


class Summary(BaseModel):
    total: float
    count: int
    by_category: dict
