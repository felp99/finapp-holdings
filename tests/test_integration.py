"""
Integration tests — these call the real yfinance API and require internet access.

Run with:
    pytest tests/test_integration.py -m integration -v

Excluded from the default test run (pytest tests/) to keep CI offline and fast.
"""

import pytest
from datetime import datetime, timezone

from src.service import fetch_ticker

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
