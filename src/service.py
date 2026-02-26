from datetime import datetime, timedelta, timezone
import requests
import yfinance as yf
from .models import (
    PricePoint, MultiplierPoint, TickerResponse, TickerSearchResult, TickerSearchResponse, SelicResponse,
    TickerPriceResponse,
)

BCB_SELIC_URL = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.11/dados"
INTERVAL = "1d"

def fetch_ticker(ticker: str, start: datetime, end: datetime | None) -> TickerResponse:
    if end is None:
        end = datetime.now(tz=timezone.utc)

    t = yf.Ticker(ticker)
    df = t.history(start=start, end=end, interval=INTERVAL)

    if df.empty:
        return TickerResponse(prices=[], multipliers=[])

    closes = df["Close"]
    # Normalize index to timezone-naive UTC datetimes
    datetimes = closes.index.tz_convert("UTC").tz_localize(None).to_pydatetime()
    base = closes.iloc[0]

    prices = [PricePoint(datetime=dt, price=float(p)) for dt, p in zip(datetimes, closes)]
    multipliers = [MultiplierPoint(datetime=dt, value=float(p / base)) for dt, p in zip(datetimes, closes)]

    return TickerResponse(prices=prices, multipliers=multipliers)


def fetch_last_price(ticker: str) -> TickerPriceResponse:
    t = yf.Ticker(ticker)
    df = t.history(period="5d", interval=INTERVAL)

    if df.empty:
        raise ValueError(f"No price data found for ticker '{ticker}'")

    last_row = df["Close"].iloc[-1]
    last_dt = df.index[-1].tz_convert("UTC").tz_localize(None).to_pydatetime()

    return TickerPriceResponse(ticker=ticker, datetime=last_dt, price=float(last_row))

def _ir_rate(days: int) -> float:
    """Tabela regressiva de IR para renda fixa (prazo desde o aporte)."""
    if days <= 180:
        return 0.225
    elif days <= 360:
        return 0.20
    elif days <= 720:
        return 0.175
    return 0.15


def fetch_selic(
    start: datetime,
    end: datetime | None,
    ir: bool = False,
    percentage: float = 100.0,
) -> SelicResponse:
    """
    Fetches the daily SELIC rate from BCB and returns a compounded multiplier series.

    Args:
        start: Start date of the investment.
        end: End date (defaults to today).
        ir: If True, applies Imposto de Renda on the gain at each point (simulating redemption).
        percentage: CDB percentage of SELIC (e.g. 103.0 for a CDB that pays 103% of SELIC).
    """
    if end is None:
        end = datetime.now()

    params = {
        "formato": "json",
        "dataInicial": start.strftime("%d/%m/%Y"),
        "dataFinal": end.strftime("%d/%m/%Y"),
    }
    resp = requests.get(BCB_SELIC_URL, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    cumulative = 1.0
    multipliers = []

    for point in data:
        dt = datetime.strptime(point["data"], "%d/%m/%Y")
        # daily_rate: BCB returns values already in % (e.g. 0.0519 = 0.0519% per day)
        daily_rate = float(point["valor"]) / 100.0 * (percentage / 100.0)
        cumulative *= 1.0 + daily_rate

        if ir:
            days_elapsed = (dt - start).days
            rate = _ir_rate(days_elapsed)
            gain = cumulative - 1.0
            net_value = 1.0 + gain * (1.0 - rate)
        else:
            net_value = cumulative

        multipliers.append(MultiplierPoint(datetime=dt, value=net_value))

    # BCB only publishes business days; ffill the last known value up to end
    if multipliers:
        last_dt = multipliers[-1].datetime
        last_value = multipliers[-1].value
        current = last_dt + timedelta(days=1)
        while current.date() <= end.date():
            multipliers.append(MultiplierPoint(datetime=current, value=last_value))
            current += timedelta(days=1)

    return SelicResponse(multipliers=multipliers)

def search_tickers(query: str, max_results: int = 10) -> TickerSearchResponse:
    search = yf.Search(query, max_results=max_results)
    results = [
        TickerSearchResult(
            symbol=q["symbol"],
            name=q.get("longname") or q.get("shortname") or q["symbol"],
            type=q.get("quoteType", ""),
            exchange=q.get("exchDisp") or q.get("exchange", ""),
        )
        for q in search.quotes
    ]
    return TickerSearchResponse(results=results)
