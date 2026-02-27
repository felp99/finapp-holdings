# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Setup
python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt

# Run dev server (requires API_KEY env var)
export API_KEY=dev-key
uvicorn src.app.main:app --reload

# Run all tests (offline, uses mocks)
pytest tests/test_analysis.py

# Run a single test
pytest tests/test_analysis.py::test_ticker_investment

# Format
python -m black src
```

API docs are auto-generated at `http://localhost:8000/docs` when the server is running.

## Architecture

The app is a FastAPI service that simulates investment capital growth over time.

**Request flow:**
1. `POST /ticker` in `src/app/routes.py` — validates bearer token via `get_api_key` dependency (`src/app/dependencies.py`), parses `TickerRequestModel`
2. Instantiates `TickerInvestment` from `src/analysis/investments.py`
3. Returns `list[CapitalPointModel]` (date + capital) from `investment.result.df_capital_cumprod`

**Analytics layer (`src/analysis/investments.py`):**

- `Data` — plain holder for four DataFrames: `df` (daily factor), `df_cumprod` (cumulative factor), `df_capital` (flat capital), `df_capital_cumprod` (compounded capital)
- `Investment` (abstract) — computes `result` and `default` `Data` objects on init; calls `generate_df()` which subclasses must implement
- `TickerInvestment` — fetches OHLCV from yfinance, converts `Close` to daily pct-change factors
- `SelicInvestment` — fetches the full SELIC daily series from BCB (`api.bcb.gov.br/dados/serie/bcdata.sgs.11/dados`) and trims to the requested window

**Pydantic models (`src/analysis/entities.py`):**
- `TickerRequestModel` — request body (`ticker`, `value`, optional `start`/`end`)
- `CapitalPointModel` — response item (`date`, `capital`)

**Auth (`src/app/dependencies.py`):** `get_api_key` reads `API_KEY` from the environment and validates `Authorization: Bearer <token>` on every request.

## Known discrepancy

`Dockerfile` and `fly.toml` still launch with `flask --app src.app.main run`, but the app uses FastAPI/uvicorn. The correct production command is `uvicorn src.app.main:app --host=0.0.0.0 --port=8080`.

## Conventions

- Commit messages follow `<type>: <summary>` (e.g. `feat:`, `fix:`, `docs:`, `chore:`)
- Keep FastAPI endpoints thin; push calculations into `src/analysis/`
- 4-space indent, 120-char soft limit, snake_case functions, PascalCase models
- Only update `requirements.txt` (`pip freeze > requirements.txt`) when intentionally bumping packages
- Tests mock both `analysis.investments.yfinance.Ticker` and `analysis.investments.requests.get` to stay deterministic and offline
