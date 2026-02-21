from fastapi import APIRouter, Depends, HTTPException, Query, status
from ..models import TickerRequest, TickerResponse, TickerSearchResponse
from ..service import fetch_ticker, search_tickers
from .dependencies import get_api_key

router = APIRouter(tags=["Ticker"])


@router.post("/ticker", response_model=TickerResponse, dependencies=[Depends(get_api_key)])
def get_ticker(payload: TickerRequest) -> TickerResponse:
    try:
        return fetch_ticker(payload.ticker, payload.start, payload.end)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get("/tickers/search", response_model=TickerSearchResponse, dependencies=[Depends(get_api_key)])
def get_tickers_search(q: str = Query(..., min_length=1, description="Search query")) -> TickerSearchResponse:
    try:
        return search_tickers(q)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
