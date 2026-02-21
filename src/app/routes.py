from fastapi import APIRouter, Depends, HTTPException, status
from ..models import TickerRequest, TickerResponse
from ..service import fetch_ticker
from .dependencies import get_api_key

router = APIRouter(tags=["Ticker"])


@router.post("/ticker", response_model=TickerResponse, dependencies=[Depends(get_api_key)])
def get_ticker(payload: TickerRequest) -> TickerResponse:
    try:
        return fetch_ticker(payload.ticker, payload.start, payload.end)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
