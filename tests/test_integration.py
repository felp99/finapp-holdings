"""
Integration tests — these call the real yfinance API and require internet access.

Run with:
    pytest tests/test_integration.py -m integration -v

Excluded from the default test run (pytest tests/) to keep CI offline and fast.
"""

import pytest
from datetime import datetime, timezone

from src.service import fetch_ticker, search_tickers

START = datetime(2024, 1, 1, tzinfo=timezone.utc)
END = datetime(2024, 1, 8, tzinfo=timezone.utc)  # one week


@pytest.mark.integration
def test_btc_usd_returns_data():
    result = fetch_ticker("BTC-USD", START, END)

    assert len(result.prices) > 0
    assert len(result.multipliers) > 0


@pytest.mark.integration
def test_eth_usd_returns_data():
    result = fetch_ticker("ETH-USD", START, END)

    assert len(result.prices) > 0


@pytest.mark.integration
def test_aapl_returns_data():
    result = fetch_ticker("AAPL", START, END)

    assert len(result.prices) > 0


@pytest.mark.integration
def test_multipliers_first_is_one():
    result = fetch_ticker("BTC-USD", START, END)

    assert result.multipliers[0].value == pytest.approx(1.0)


@pytest.mark.integration
def test_prices_and_multipliers_same_length():
    result = fetch_ticker("BTC-USD", START, END)

    assert len(result.prices) == len(result.multipliers)


@pytest.mark.integration
def test_datetimes_are_timezone_naive():
    result = fetch_ticker("BTC-USD", START, END)

    for point in result.prices:
        assert point.datetime.tzinfo is None


@pytest.mark.integration
def test_prices_are_positive():
    result = fetch_ticker("BTC-USD", START, END)

    for point in result.prices:
        assert point.price > 0


@pytest.mark.integration
def test_invalid_ticker_returns_empty():
    result = fetch_ticker("INVALID-TICKER-XYZ", START, END)

    assert result.prices == []
    assert result.multipliers == []


# ---------------------------------------------------------------------------
# search_tickers
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_search_bitcoin_returns_btc_usd():
    result = search_tickers("bitcoin")

    symbols = [r.symbol for r in result.results]
    assert "BTC-USD" in symbols


@pytest.mark.integration
def test_search_apple_returns_aapl():
    result = search_tickers("apple")

    symbols = [r.symbol for r in result.results]
    assert "AAPL" in symbols


@pytest.mark.integration
def test_search_results_have_required_fields():
    result = search_tickers("bitcoin")

    for r in result.results:
        assert r.symbol
        assert r.name
        assert r.type
        # exchange may be empty for some instruments, so we just check it exists
        assert hasattr(r, "exchange")


@pytest.mark.integration
def test_search_returns_multiple_results():
    result = search_tickers("bitcoin")

    assert len(result.results) > 1


@pytest.mark.integration
def test_search_no_match_returns_empty():
    result = search_tickers("zzznomatchatall123")

    assert result.results == []
