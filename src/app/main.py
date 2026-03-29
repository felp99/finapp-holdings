import logging

from fastapi import FastAPI
from .routes import router
from ..binance.routes import router as binance_router

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Holdings API",
    description="Hourly price history and cumulative multipliers for any ticker.",
    version="2.0.0",
)
app.include_router(router)
app.include_router(binance_router)
