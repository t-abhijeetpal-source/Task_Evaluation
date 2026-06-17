"""Pydantic schemas — the validation layer (API boundary contract).

Only structural/type validation lives here (required + numeric + string).
Business rules (amount > 0, currency supported) live in the service layer so
they can return the specific status codes the API contract requires.
"""

from pydantic import BaseModel, ConfigDict, Field


class ConvertRequest(BaseModel):
    """Request body for POST /convert.

    `from` is a Python keyword, so it is accepted via alias and stored as
    `from_currency`. `populate_by_name` lets tests build it either way.
    """

    amount: float = Field(..., description="Amount to convert (validated > 0 in service)")
    from_currency: str = Field(..., alias="from", description="Source currency code")
    to_currency: str = Field(..., alias="to", description="Target currency code")

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={"example": {"amount": 100, "from": "USD", "to": "INR"}},
    )


class ConvertResponse(BaseModel):
    """Response body for a successful conversion (documents the contract)."""

    converted_amount: float
    from_currency: str = Field(..., alias="from")
    to_currency: str = Field(..., alias="to")

    model_config = ConfigDict(populate_by_name=True)
