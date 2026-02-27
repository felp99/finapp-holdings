import os
import pytest
from datetime import datetime, timezone
from unittest.mock import patch

from fastapi.testclient import TestClient

from src.app.main import app
from src.models import (
    PricePoint, MultiplierPoint, TickerResponse, TickerSearchResult, TickerSearchResponse, SelicResponse,
    TickerPriceResponse,
)

client = TestClient(app, raise_server_exceptions=False)

VALID_TOKEN = "test-key"

MOCK_RESPONSE = TickerResponse(
    prices=[PricePoint(datetime=datetime(2024, 1, 1, 10, tzinfo=timezone.utc), price=42000.0)],
    multipliers=[MultiplierPoint(datetime=datetime(2024, 1, 1, 10, tzinfo=timezone.utc), value=1.0)],
)

TICKER_PARAMS = {"ticker": "BTC-USD", "start": "2024-01-01T00:00:00Z"}


@pytest.fixture(autouse=True)
def set_api_key(monkeypatch):
    monkeypatch.setenv("API_KEY", VALID_TOKEN)


def test_valid_token_returns_200():
    with patch("src.app.routes.fetch_ticker", return_value=MOCK_RESPONSE):
        response = client.get(
            "/ticker",
            params=TICKER_PARAMS,
            headers={"Authorization": f"Bearer {VALID_TOKEN}"},
        )
    assert response.status_code == 200
    body = response.json()
    assert "prices" in body
    assert "multipliers" in body
    assert len(body["prices"]) == 1
    assert len(body["multipliers"]) == 1


def test_missing_token_returns_403():
    response = client.get("/ticker", params=TICKER_PARAMS)
    assert response.status_code == 403


def test_wrong_token_returns_401():
    response = client.get(
        "/ticker",
        params=TICKER_PARAMS,
        headers={"Authorization": "Bearer wrong-key"},
    )
    assert response.status_code == 401


# ---------------------------------------------------------------------------
# GET /tickers/search
# ---------------------------------------------------------------------------

MOCK_SEARCH_RESPONSE = TickerSearchResponse(results=[
    TickerSearchResult(symbol="BTC-USD", name="Bitcoin USD", type="CRYPTOCURRENCY", exchange="CCC"),
    TickerSearchResult(symbol="BCH-USD", name="Bitcoin Cash USD", type="CRYPTOCURRENCY", exchange="CCC"),
])

AUTH = {"Authorization": f"Bearer {VALID_TOKEN}"}


def test_search_returns_200():
    with patch("src.app.routes.search_tickers", return_value=MOCK_SEARCH_RESPONSE):
        response = client.get("/tickers/search", params={"q": "bitcoin"}, headers=AUTH)
    assert response.status_code == 200
    body = response.json()
    assert "results" in body
    assert len(body["results"]) == 2


def test_search_result_fields():
    with patch("src.app.routes.search_tickers", return_value=MOCK_SEARCH_RESPONSE):
        response = client.get("/tickers/search", params={"q": "bitcoin"}, headers=AUTH)
    first = response.json()["results"][0]
    assert first["symbol"] == "BTC-USD"
    assert first["name"] == "Bitcoin USD"
    assert first["type"] == "CRYPTOCURRENCY"
    assert first["exchange"] == "CCC"


def test_search_missing_query_returns_422():
    response = client.get("/tickers/search", headers=AUTH)
    assert response.status_code == 422


def test_search_missing_token_returns_403():
    response = client.get("/tickers/search", params={"q": "bitcoin"})
    assert response.status_code == 403


def test_search_wrong_token_returns_401():
    response = client.get(
        "/tickers/search",
        params={"q": "bitcoin"},
        headers={"Authorization": "Bearer wrong-key"},
    )
    assert response.status_code == 401


def test_search_empty_results():
    empty = TickerSearchResponse(results=[])
    with patch("src.app.routes.search_tickers", return_value=empty):
        response = client.get("/tickers/search", params={"q": "zzznomatch"}, headers=AUTH)
    assert response.status_code == 200
    assert response.json()["results"] == []


def test_search_service_error_returns_500():
    with patch("src.app.routes.search_tickers", side_effect=RuntimeError("upstream failure")):
        response = client.get("/tickers/search", params={"q": "bitcoin"}, headers=AUTH)
    assert response.status_code == 500


# ---------------------------------------------------------------------------
# GET /ticker — error path
# ---------------------------------------------------------------------------


def test_ticker_missing_params_returns_422():
    response = client.get("/ticker", headers=AUTH)
    assert response.status_code == 422


def test_ticker_service_error_returns_500():
    with patch("src.app.routes.fetch_ticker", side_effect=RuntimeError("yfinance down")):
        response = client.get("/ticker", params=TICKER_PARAMS, headers=AUTH)
    assert response.status_code == 500


# ---------------------------------------------------------------------------
# GET /selic
# ---------------------------------------------------------------------------

MOCK_SELIC_RESPONSE = SelicResponse(
    multipliers=[
        MultiplierPoint(datetime=datetime(2024, 1, 2, tzinfo=timezone.utc), value=1.0),
        MultiplierPoint(datetime=datetime(2024, 1, 3, tzinfo=timezone.utc), value=1.000369),
    ]
)

SELIC_PARAMS = {"start": "2024-01-01"}


def test_selic_returns_200():
    with patch("src.app.routes.fetch_selic", return_value=MOCK_SELIC_RESPONSE):
        response = client.get("/selic", params=SELIC_PARAMS, headers=AUTH)
    assert response.status_code == 200
    body = response.json()
    assert "multipliers" in body
    assert len(body["multipliers"]) == 2


def test_selic_multiplier_fields():
    with patch("src.app.routes.fetch_selic", return_value=MOCK_SELIC_RESPONSE):
        response = client.get("/selic", params=SELIC_PARAMS, headers=AUTH)
    first = response.json()["multipliers"][0]
    assert "datetime" in first
    assert "value" in first
    assert first["value"] == pytest.approx(1.0)


def test_selic_missing_start_returns_422():
    response = client.get("/selic", headers=AUTH)
    assert response.status_code == 422


def test_selic_missing_token_returns_403():
    response = client.get("/selic", params=SELIC_PARAMS)
    assert response.status_code == 403


def test_selic_wrong_token_returns_401():
    response = client.get("/selic", params=SELIC_PARAMS, headers={"Authorization": "Bearer wrong-key"})
    assert response.status_code == 401


def test_selic_with_ir_flag():
    with patch("src.app.routes.fetch_selic", return_value=MOCK_SELIC_RESPONSE) as mock_fn:
        response = client.get("/selic", params={**SELIC_PARAMS, "ir": "true"}, headers=AUTH)
    assert response.status_code == 200
    _, kwargs = mock_fn.call_args
    assert kwargs["ir"] is True


def test_selic_with_percentage():
    with patch("src.app.routes.fetch_selic", return_value=MOCK_SELIC_RESPONSE) as mock_fn:
        response = client.get("/selic", params={**SELIC_PARAMS, "percentage": "103"}, headers=AUTH)
    assert response.status_code == 200
    _, kwargs = mock_fn.call_args
    assert kwargs["percentage"] == pytest.approx(103.0)


def test_selic_with_explicit_end():
    with patch("src.app.routes.fetch_selic", return_value=MOCK_SELIC_RESPONSE):
        response = client.get("/selic", params={"start": "2024-01-01", "end": "2024-01-31"}, headers=AUTH)
    assert response.status_code == 200


def test_selic_service_error_returns_500():
    with patch("src.app.routes.fetch_selic", side_effect=RuntimeError("BCB unreachable")):
        response = client.get("/selic", params=SELIC_PARAMS, headers=AUTH)
    assert response.status_code == 500
    
# ---------------------------------------------------------------------------
# GET /ticker/price
# ---------------------------------------------------------------------------

MOCK_PRICE_RESPONSE = TickerPriceResponse(
    ticker="BTC-USD",
    datetime=datetime(2024, 1, 3, 10, tzinfo=timezone.utc),
    price=42000.0,
)


PRICE_PARAMS = {"ticker": "BTC-USD", "date": "2024-01-03T00:00:00Z"}


def test_ticker_price_returns_200():
    with patch("src.app.routes.fetch_last_price", return_value=MOCK_PRICE_RESPONSE):
        response = client.get("/ticker/price", params=PRICE_PARAMS, headers=AUTH)
    assert response.status_code == 200
    body = response.json()
    assert body["ticker"] == "BTC-USD"
    assert body["price"] == pytest.approx(42000.0)
    assert "datetime" in body


def test_ticker_price_missing_date_returns_422():
    response = client.get("/ticker/price", params={"ticker": "BTC-USD"}, headers=AUTH)
    assert response.status_code == 422


def test_ticker_price_missing_token_returns_403():
    response = client.get("/ticker/price", params=PRICE_PARAMS)
    assert response.status_code == 403


def test_ticker_price_unknown_ticker_returns_404():
    with patch("src.app.routes.fetch_last_price", side_effect=ValueError("No price data found for ticker 'UNKNOWN' on 2024-01-03")):
        response = client.get("/ticker/price", params={"ticker": "UNKNOWN", "date": "2024-01-03T00:00:00Z"}, headers=AUTH)
    assert response.status_code == 404


def test_ticker_price_service_error_returns_500():
    with patch("src.app.routes.fetch_last_price", side_effect=RuntimeError("yfinance down")):
        response = client.get("/ticker/price", params=PRICE_PARAMS, headers=AUTH)
    assert response.status_code == 500
