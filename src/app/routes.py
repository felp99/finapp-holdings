from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from ..models import TickerResponse, TickerSearchResponse, SelicResponse, TickerPriceResponse
from ..service import fetch_ticker, search_tickers, fetch_selic, fetch_last_price
from .dependencies import get_api_key

router = APIRouter(tags=["Ticker"])


@router.get("/ticker", response_model=TickerResponse, dependencies=[Depends(get_api_key)])
def get_ticker(
    ticker: str = Query(..., description="Ticker symbol, e.g. BTC-USD"),
    start: datetime = Query(..., description="Start datetime (ISO 8601)"),
    end: datetime = Query(default=None, description="End datetime (ISO 8601), defaults to now"),
) -> TickerResponse:
    try:
        return fetch_ticker(ticker, start, end)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get("/ticker/price", response_model=TickerPriceResponse, dependencies=[Depends(get_api_key)])
def get_ticker_price(
    ticker: str = Query(..., description="Ticker symbol, e.g. BTC-USD"),
    date: datetime = Query(..., description="Date to fetch price for (ISO 8601)"),
) -> TickerPriceResponse:
    try:
        return fetch_last_price(ticker, date)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get("/tickers/search", response_model=TickerSearchResponse, dependencies=[Depends(get_api_key)])
def get_tickers_search(q: str = Query(..., min_length=1, description="Search query")) -> TickerSearchResponse:
    try:
        return search_tickers(q)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc

@router.get("/selic", response_model=SelicResponse, dependencies=[Depends(get_api_key)])
def get_selic(
    start: date = Query(..., description="Start date (YYYY-MM-DD)"),
    end: date = Query(default=None, description="End date (YYYY-MM-DD), defaults to today"),
    ir: bool = Query(default=False, description="Apply Imposto de Renda on gains at each point"),
    percentage: float = Query(default=100.0, description="CDB percentage of SELIC, e.g. 103 for 103% of SELIC"),
) -> SelicResponse:
    try:
        start_dt = datetime.combine(start, datetime.min.time())
        end_dt = datetime.combine(end, datetime.min.time()) if end else None
        return fetch_selic(start=start_dt, end=end_dt, ir=ir, percentage=percentage)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
