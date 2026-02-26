from datetime import datetime
from enum import Enum
from pydantic import BaseModel

class PricePoint(BaseModel):
    datetime: datetime
    price: float


class MultiplierPoint(BaseModel):
    datetime: datetime
    value: float


class TickerResponse(BaseModel):
    prices: list[PricePoint]
    multipliers: list[MultiplierPoint]


class TickerSearchResult(BaseModel):
    symbol: str
    name: str
    type: str
    exchange: str


class TickerSearchResponse(BaseModel):
    results: list[TickerSearchResult]


class SelicResponse(BaseModel):
    multipliers: list[MultiplierPoint]

class TickerPriceResponse(BaseModel):
    ticker: str
    datetime: datetime
    price: float
