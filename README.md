# finapp-holdings

## Start

```bash
python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
export API_KEY=dev-key
uvicorn src.app.main:app --reload
```

API docs: http://localhost:8000/docs

## Test

```bash
pytest tests/ -v
```
