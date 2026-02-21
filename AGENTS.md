# Repository Guidelines

## Project Structure & Module Organization
Application code lives in `src/`. `src/analysis/entities.py` implements analytics models and helpers, while `tests/test_analysis.py` houses the regression suite. `src/app/main.py` hosts the Flask API (currently `/ticker`), while system diagrams stay inside `docs/` and runtime config files (`Dockerfile`, `fly.toml`, `mise.toml`) remain at the repo root for easy provisioning.

## Build, Test, and Development Commands
Create a virtualenv and install dependencies with `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`. Launch the API from the repo root via `python -m src.app.main` (Python treats `src/` as a package, so no manual `sys.path` hacks are required). Validate analytics flows with `python -m unittest tests.test_analysis`; the suite now replaces remote Yahoo Finance and BCB calls with mocks, so it runs quickly and offline. Only run `pip freeze > requirements.txt` when you intentionally bump packages so dependency diffs stay meaningful.

## Coding Style & Naming Conventions
Stick to PEP 8 defaults: four-space indentation, 120-character soft limit, snake_case functions, and PascalCase models such as `TickerInvestment`. Keep Flask routes thin and push calculations into `analysis` helpers. Favor explicit imports and short docstrings for non-obvious math. Format with `python -m black src` (optional but recommended) before committing so diffs remain reviewable.

## Testing Guidelines
Unit tests rely on `unittest`. Place new suites under `tests/` using `Test<Class>` containers and `test_*` methods. Keep mocking strategies in mind—`tests/test_analysis.py` shows how to patch yfinance and `requests.get` so suites stay deterministic and offline-friendly. Always run `python -m unittest` (or `python -m unittest discover -s tests`) before submitting and document any new external dependencies in the PR.

## Commit & Pull Request Guidelines
History follows `<type>: <summary>` (e.g., `feat: flask api`, `docs: youtube mind map`), so keep using lowercase conventional types such as `feat`, `fix`, `docs`, or `chore`. PRs should link their issue, describe API/analytics impact, and attach sample `/investment-ticker` payloads or CLI screenshots. Keep diffs atomic—separate analytics changes from dependency bumps—to simplify code review and rollback.

## Security & Configuration Tips
`src/app/main.py` guards routes with `API_KEY`, so export it (`export API_KEY=dev-key`) or store it in `.env` loaded through `python-dotenv`. Do not commit keys or portfolio data—manage secrets via environment variables or Fly (`fly secrets set API_KEY=...`). Sanitize request/response logs before sharing to protect investor strategies.
