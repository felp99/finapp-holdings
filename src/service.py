from datetime import datetime, timedelta, timezone
import yfinance as yf
from .models import PricePoint, MultiplierPoint, TickerResponse, TickerSearchResult, TickerSearchResponse

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
