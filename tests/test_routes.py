import os
import pytest
from datetime import datetime, timezone
from unittest.mock import patch

from fastapi.testclient import TestClient

from src.app.main import app
from src.models import PricePoint, MultiplierPoint, TickerResponse, TickerSearchResult, TickerSearchResponse

client = TestClient(app, raise_server_exceptions=False)

VALID_TOKEN = "test-key"

MOCK_RESPONSE = TickerResponse(
    prices=[PricePoint(datetime=datetime(2024, 1, 1, 10, tzinfo=timezone.utc), price=42000.0)],
    multipliers=[MultiplierPoint(datetime=datetime(2024, 1, 1, 10, tzinfo=timezone.utc), value=1.0)],
)

PAYLOAD = {"ticker": "BTC-USD", "start": "2024-01-01T00:00:00Z"}


@pytest.fixture(autouse=True)
def set_api_key(monkeypatch):
    monkeypatch.setenv("API_KEY", VALID_TOKEN)


def test_valid_token_returns_200():
    with patch("src.app.routes.fetch_ticker", return_value=MOCK_RESPONSE):
        response = client.post(
            "/ticker",
            json=PAYLOAD,
            headers={"Authorization": f"Bearer {VALID_TOKEN}"},
        )
    assert response.status_code == 200
    body = response.json()
    assert "prices" in body
    assert "multipliers" in body
    assert len(body["prices"]) == 1
    assert len(body["multipliers"]) == 1


def test_missing_token_returns_403():
    response = client.post("/ticker", json=PAYLOAD)
    assert response.status_code == 403


def test_wrong_token_returns_401():
    response = client.post(
        "/ticker",
        json=PAYLOAD,
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
