# Job Hunt OS (Single-User MVP)

A tiny FastAPI + SQL app to track your job applications: filters, pagination, CSV export, simple API-key auth, tests, and CI.

## Features
- CRUD for applications with validation
- Filters: search (company/role), stage, status
- Pagination + ordering (created_at/updated_at/next_action_date)
- CSV export with the same filters
- Single API key via `X-API-Key` header for writes
- SQLite locally, easy switch to Postgres (Week 2)
- Tests with `pytest`
- GitHub Actions runs tests on push
- OpenAPI docs at `/docs`

## Tech
- FastAPI, SQLAlchemy 2.x, Pydantic v2
- python-dotenv for env management
- SQLite (default) → Postgres (Week 2)
- httpx/TestClient (or FastAPI TestClient) for tests

## Run locally
```bash
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # set API_KEY and DATABASE_URL
uvicorn app.main:app --reload
```

Go to: http://127.0.0.1:8000/docs

## API usage (curl)
```bash
# Health
curl -s http://127.0.0.1:8000/health

# Create (requires API key)
curl -s -X POST http://127.0.0.1:8000/applications       -H 'Content-Type: application/json'       -H 'X-API-Key: REPLACE_ME'       -d '{
    "company":"Acme",
    "role":"Backend Developer",
    "location":"NYC, NY",
    "source":"LinkedIn",
    "link":"https://jobs.acme.com/123",
    "salary_min":100000,
    "salary_max":130000,
    "employment_type":"full-time",
    "stage":"applied",
    "status":"active",
    "next_action_date":"2025-09-10",
    "notes":"Follow up with recruiter"
  }'

# List with filters + pagination
curl -s "http://127.0.0.1:8000/applications?search=acme&stage=applied&page=1&page_size=20&order_by=created_at&order_dir=desc"

# Export CSV (same filters)
curl -s "http://127.0.0.1:8000/export.csv?status=active" -o export.csv
```

## Tests
```bash
pytest -q
```

## CI (GitHub Actions)
- On push, `pytest` runs. See `.github/workflows/ci.yml`.

## Week 2 (Postgres + Deploy)
- Use `docker-compose.yml` to run Postgres.
- Switch `DATABASE_URL` to Postgres and migrate data.
- Deploy to Render/Railway/Fly, set env vars, and verify.

---
Screenshots and Loom links go here later.
