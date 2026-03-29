import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from ..app.dependencies import get_api_key
from .client import create_finapp_event, place_order

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/binance", tags=["Binance"])


class BinanceBuyRequest(BaseModel):
    ticker: str
    value: float


@router.post("/buy", dependencies=[Depends(get_api_key)])
def binance_buy_test(body: BinanceBuyRequest) -> dict:
    """Test a Binance market buy order without executing it (uses /api/v3/order/test)."""
    try:
        result = place_order(body.ticker, body.value)
        logger.info("Binance order: %s", result)

        if result.get("status") == "FILLED":
            event = create_finapp_event(result, body.value, body.ticker)
            logger.info("FinApp event: %s", event)
            return {"binance_order": result, "finapp_event": event}
        else:
            return {"binance_order": result}
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc