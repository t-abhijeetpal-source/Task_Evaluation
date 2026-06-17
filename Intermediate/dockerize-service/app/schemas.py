"""Pydantic schemas — validation layer."""

from pydantic import BaseModel, ConfigDict, Field


class ConvertRequest(BaseModel):
    amount: float = Field(..., description="Amount to convert (validated > 0 in service)")
    from_currency: str = Field(..., alias="from")
    to_currency: str = Field(..., alias="to")

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={"example": {"amount": 100, "from": "USD", "to": "INR"}},
    )
