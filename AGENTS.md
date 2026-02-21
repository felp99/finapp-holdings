# Repository Guidelines

## Project Structure & Module Organization
Application code lives in `src/`. `src/analysis/entities.py` implements analytics models and helpers, while `tests/test_analysis.py` houses the regression suite. `src/app/main.py` hosts the FastAPI service (currently `/ticker`), while system diagrams stay inside `docs/` and runtime config files (`Dockerfile`, `fly.toml`, `mise.toml`) remain at the repo root for easy provisioning.

## Build, Test, and Development Commands
Create a virtualenv and install dependencies with `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt` (FastAPI/uvicorn are included). Launch the API from the repo root with `uvicorn src.app.main:app --reload`; `src/` is already a package, so no PYTHONPATH tweaks are needed. Validate analytics flows with `pytest tests/test_analysis.py`; the suite mocks Yahoo Finance and BCB traffic so it runs quickly and offline. Only run `pip freeze > requirements.txt` when you intentionally bump packages so dependency diffs stay meaningful.

## API Documentation & Swagger
FastAPI auto-generates OpenAPI docs—start the dev server and open `http://localhost:8000/docs` (Swagger UI) or `http://localhost:8000/redoc`. Keep the Pydantic models and route metadata in `src/app/main.py` current whenever you add fields, and note any new security requirements in the dependency that enforces the API key.

## Coding Style & Naming Conventions
Stick to PEP 8 defaults: four-space indentation, 120-character soft limit, snake_case functions, and PascalCase models such as `TickerInvestment`. Keep FastAPI endpoints thin and push calculations into `analysis` helpers. Favor explicit imports and short docstrings for non-obvious math. Format with `python -m black src` (optional but recommended) before committing so diffs remain reviewable.

## Testing Guidelines
Unit tests rely on `pytest`. Place new suites under `tests/` and follow the `test_*` naming conventions for files and functions. Keep mocking strategies in mind—`tests/test_analysis.py` shows how to patch yfinance and `requests.get` so suites stay deterministic and offline-friendly. Always run `pytest` (or `pytest tests/`) before submitting and document any new external dependencies in the PR.

## Commit & Pull Request Guidelines
History follows `<type>: <summary>` (e.g., `feat: flask api`, `docs: youtube mind map`), so keep using lowercase conventional types such as `feat`, `fix`, `docs`, or `chore`. PRs should link their issue, describe API/analytics impact, and attach sample `/ticker` payloads or CLI screenshots. Keep diffs atomic—separate analytics changes from dependency bumps—to simplify code review and rollback.

## Security & Configuration Tips
`src/app/main.py` guards routes with `API_KEY`, so export it (`export API_KEY=dev-key`) before running uvicorn or load it via Docker/Fly secrets. Clients must send the key in `Authorization: Bearer <API_KEY>` for every request. Do not commit keys or portfolio data—manage secrets via environment variables or Fly (`fly secrets set API_KEY=...`). Sanitize request/response logs before sharing to protect investor strategies.
