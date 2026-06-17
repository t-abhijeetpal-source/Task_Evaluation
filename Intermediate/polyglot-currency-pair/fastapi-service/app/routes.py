"""Route layer — HTTP only.

Maps the request to the service and the service's typed errors to the exact
status codes / bodies required by the API contract. No conversion logic here.
"""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app import services
from app.schemas import ConvertRequest

router = APIRouter()


@router.post("/convert")
def convert(req: ConvertRequest):
    """POST /convert — convert an amount between supported currencies."""
    try:
        result = services.convert(req.amount, req.from_currency, req.to_currency)
    except services.InvalidAmountError:
        return JSONResponse(status_code=422, content={"error": "Amount must be positive"})
    except services.UnsupportedCurrencyError:
        return JSONResponse(status_code=400, content={"error": "Unsupported currency"})

    return {
        "converted_amount": result,
        "from": req.from_currency.upper(),
        "to": req.to_currency.upper(),
    }
