from fastapi import FastAPI
from .routes import router

app = FastAPI(
    title="Holdings API",
    description="Hourly price history and cumulative multipliers for any ticker.",
    version="2.0.0",
)
app.include_router(router)
