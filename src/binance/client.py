import hashlib
import hmac
import time
from datetime import datetime, timezone
from os import getenv

import requests

from .finapp import Finapp

BINANCE_BASE_URL = "https://api.binance.com"


def _sign(params: dict, secret: str) -> str:
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return hmac.new(secret.encode("utf-8"), query.encode("utf-8"), hashlib.sha256).hexdigest()


def place_order(ticker: str, value: float) -> dict:
    api_key = getenv("BINANCE_API_KEY", "")
    api_secret = getenv("BINANCE_API_SECRET", "")
    endpoint = "/api/v3/order"

    params = {
        "symbol": ticker,
        "side": "BUY",
        "type": "MARKET",
        "quoteOrderQty": value,
        "timestamp": int(time.time() * 1000),
    }
    params["signature"] = _sign(params, api_secret)

    resp = requests.post(
        f"{BINANCE_BASE_URL}{endpoint}",
        params=params,
        headers={"X-MBX-APIKEY": api_key},
        timeout=30,
    )
    if not resp.ok:
        raise ValueError(resp.json())
    return resp.json()


def create_finapp_event(order: dict, value: float, ticker: str) -> dict:
    finapp = Finapp()
    token = finapp.login()
    asset_id = getenv("FINAPP_ASSET_ID", "")
    card_id = getenv("FINAPP_CARD_ID", "")

    executed_qty = float(order.get("executedQty", 0))
    quote_qty = float(order.get("cummulativeQuoteQty", value))

    fills = order.get("fills", [])
    if not fills:
        raise ValueError("Order has no fills")

    # VWAP across all fills — handles partial fills at different price levels
    total_fill_quote = sum(float(f["price"]) * float(f["qty"]) for f in fills)
    total_fill_qty = sum(float(f["qty"]) for f in fills)
    asset_unit_price = total_fill_quote / total_fill_qty

    if ticker.endswith("USDT"):
        fiat_currency = "USDT"
    elif ticker.endswith("BRL"):
        fiat_currency = "BRL"
    else:
        raise ValueError(f"Invalid ticker: {ticker}")

    base_asset = ticker[: -len(fiat_currency)]
    asset_commission = sum(
        float(f["commission"]) for f in fills if f.get("commissionAsset") == base_asset
    )
    asset_unit_fees = asset_commission if asset_commission > 0 else None
    fiat_fees = (asset_commission * asset_unit_price) if asset_commission > 0 else None

    transact_time = order.get("transactTime")
    if transact_time:
        date = datetime.fromtimestamp(transact_time / 1000, tz=timezone.utc).isoformat()
    else:
        date = datetime.now(tz=timezone.utc).isoformat()

    body = {
        "asset_event": {
            "event_type": "buy",
            "date": date,
            "quantity_delta": executed_qty if executed_qty > 0 else None,
            "asset_unit_price": asset_unit_price,
            "asset_unit_price_currency": fiat_currency,
            "asset_unit_fees": asset_unit_fees,
            "fiat_amount": quote_qty,
            "fiat_fees": fiat_fees,
            "fiat_currency": fiat_currency,
            "card_id": card_id,
        }
    }

    resp = requests.post(
        f"{finapp.base_url}/api/assets/{asset_id}/asset_events",
        json=body,
        headers={"Authorization": f"Bearer {token}"},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def binance_response() -> dict:
    return {'symbol': 'BTCBRL', 'orderId': 2110420300, 'orderListId': -1, 'clientOrderId': '7iA6p8XACftO49wYzo88HK', 'transactTime': 1774805972651, 'price': '0.00000000', 'origQty': '0.00002000', 'executedQty': '0.00002000', 'origQuoteOrderQty': '10.00000000', 'cummulativeQuoteQty': '6.96418000', 'status': 'FILLED', 'timeInForce': 'GTC', 'type': 'MARKET', 'side': 'BUY', 'workingTime': 1774805972651, 'fills': [{'price': '348209.00000000', 'qty': '0.00002000', 'commission': '0.00000002', 'commissionAsset': 'BTC', 'tradeId': 58429353}], 'selfTradePreventionMode': 'EXPIRE_MAKER'}
