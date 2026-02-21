import pandas as pd
import pytest
from datetime import datetime, timezone
from unittest.mock import patch

from src.service import fetch_ticker


def _make_df(closes: list[float], start_iso: str = "2024-01-01 10:00:00+00:00") -> pd.DataFrame:
    """Build a deterministic DataFrame mimicking yfinance output."""
    freq = "1h"
    index = pd.date_range(start=start_iso, periods=len(closes), freq=freq, tz="UTC")
    return pd.DataFrame({"Close": closes}, index=index)


# ---------------------------------------------------------------------------
# Basic BTC-USD fixture (3 hourly points)
# ---------------------------------------------------------------------------

@patch("src.service.yf.Ticker")
def test_fetch_ticker_prices_length(mock_ticker_cls):
    mock_ticker_cls.return_value.history.return_value = _make_df([40000.0, 42000.0, 44000.0])

    result = fetch_ticker("BTC-USD", datetime(2024, 1, 1, tzinfo=timezone.utc), None)

    assert len(result.prices) == 3


@patch("src.service.yf.Ticker")
def test_fetch_ticker_multipliers_first_is_one(mock_ticker_cls):
    mock_ticker_cls.return_value.history.return_value = _make_df([40000.0, 42000.0, 44000.0])

    result = fetch_ticker("BTC-USD", datetime(2024, 1, 1, tzinfo=timezone.utc), None)

    assert result.multipliers[0].value == pytest.approx(1.0)


@patch("src.service.yf.Ticker")
def test_fetch_ticker_multipliers_last_value(mock_ticker_cls):
    mock_ticker_cls.return_value.history.return_value = _make_df([40000.0, 42000.0, 44000.0])

    result = fetch_ticker("BTC-USD", datetime(2024, 1, 1, tzinfo=timezone.utc), None)

    # 44000 / 40000 = 1.1
    assert result.multipliers[-1].value == pytest.approx(44000.0 / 40000.0)


@patch("src.service.yf.Ticker")
def test_fetch_ticker_empty_df_returns_empty_response(mock_ticker_cls):
    mock_ticker_cls.return_value.history.return_value = pd.DataFrame()

    result = fetch_ticker("UNKNOWN", datetime(2024, 1, 1, tzinfo=timezone.utc), None)

    assert result.prices == []
    assert result.multipliers == []


# ---------------------------------------------------------------------------
# Different tickers
# ---------------------------------------------------------------------------

@patch("src.service.yf.Ticker")
def test_fetch_ticker_eth_usd(mock_ticker_cls):
    mock_ticker_cls.return_value.history.return_value = _make_df([3000.0, 3100.0, 3200.0])

    result = fetch_ticker("ETH-USD", datetime(2024, 6, 1, tzinfo=timezone.utc), None)

    assert len(result.prices) == 3
    assert result.prices[0].price == pytest.approx(3000.0)
    assert result.prices[-1].price == pytest.approx(3200.0)


@patch("src.service.yf.Ticker")
def test_fetch_ticker_aapl_stock(mock_ticker_cls):
    mock_ticker_cls.return_value.history.return_value = _make_df([170.0, 172.5, 175.0])

    result = fetch_ticker("AAPL", datetime(2024, 3, 1, tzinfo=timezone.utc), None)

    assert len(result.prices) == 3
    assert result.multipliers[-1].value == pytest.approx(175.0 / 170.0)


@patch("src.service.yf.Ticker")
def test_fetch_ticker_spy_etf(mock_ticker_cls):
    mock_ticker_cls.return_value.history.return_value = _make_df([500.0, 502.0])

    result = fetch_ticker("SPY", datetime(2024, 9, 1, tzinfo=timezone.utc), None)

    assert result.multipliers[0].value == pytest.approx(1.0)
    assert result.multipliers[1].value == pytest.approx(502.0 / 500.0)


# ---------------------------------------------------------------------------
# Different date ranges
# ---------------------------------------------------------------------------

@patch("src.service.yf.Ticker")
def test_fetch_ticker_with_explicit_end(mock_ticker_cls):
    mock_ticker_cls.return_value.history.return_value = _make_df(
        [50000.0, 51000.0], start_iso="2023-06-01 00:00:00+00:00"
    )

    result = fetch_ticker(
        "BTC-USD",
        datetime(2023, 6, 1, tzinfo=timezone.utc),
        datetime(2023, 6, 2, tzinfo=timezone.utc),
    )

    assert len(result.prices) == 2


@patch("src.service.yf.Ticker")
def test_fetch_ticker_single_point(mock_ticker_cls):
    """A single data point should yield multiplier == 1.0."""
    mock_ticker_cls.return_value.history.return_value = _make_df([29000.0])

    result = fetch_ticker("BTC-USD", datetime(2023, 1, 1, tzinfo=timezone.utc), None)

    assert len(result.prices) == 1
    assert result.multipliers[0].value == pytest.approx(1.0)


@patch("src.service.yf.Ticker")
def test_fetch_ticker_long_range_many_points(mock_ticker_cls):
    closes = [float(100 + i) for i in range(365)]
    mock_ticker_cls.return_value.history.return_value = _make_df(
        closes, start_iso="2022-01-01 00:00:00+00:00"
    )

    result = fetch_ticker(
        "SPY",
        datetime(2022, 1, 1, tzinfo=timezone.utc),
        datetime(2023, 1, 1, tzinfo=timezone.utc),
    )

    assert len(result.prices) == 365
    assert result.multipliers[-1].value == pytest.approx(closes[-1] / closes[0])


# ---------------------------------------------------------------------------
# Datetime correctness
# ---------------------------------------------------------------------------

@patch("src.service.yf.Ticker")
def test_fetch_ticker_datetimes_are_timezone_naive(mock_ticker_cls):
    mock_ticker_cls.return_value.history.return_value = _make_df([40000.0, 41000.0])

    result = fetch_ticker("BTC-USD", datetime(2024, 1, 1, tzinfo=timezone.utc), None)

    for point in result.prices:
        assert point.datetime.tzinfo is None


@patch("src.service.yf.Ticker")
def test_fetch_ticker_prices_and_multipliers_same_length(mock_ticker_cls):
    mock_ticker_cls.return_value.history.return_value = _make_df([1.0, 2.0, 3.0, 4.0, 5.0])

    result = fetch_ticker("ETH-USD", datetime(2024, 1, 1, tzinfo=timezone.utc), None)

    assert len(result.prices) == len(result.multipliers)
