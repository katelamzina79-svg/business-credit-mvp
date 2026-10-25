# Business Credit MVP

MVP for SME business credit applications. This repository contains the backend foundation and analysis/design artifacts prepared for Days 1–2.

## Current status
- FastAPI + PostgreSQL + Docker Compose backend (`backend/`)
- SQLAlchemy models, Alembic initial migration, JWT auth and demo seed data
- Client UI: login, product selection, mock company lookup by INN, application submission, status cards and status history
- Workflow API: validated status transitions, status history and audit events
- Day 1–2 analyst documentation: `docs/`; Day 3 handoffs/demo: `docs/day3/`
- API contract: `backend/openapi_contract.md`

## Run locally
From the repository root:

```bash
cd backend
docker compose up --build
```

Then open:
- Swagger: http://localhost:8000/docs
- Health: http://localhost:8000/health

Test accounts (local demo only):
- `client@example.com` / `client123`
- `banker@example.com` / `banker123`

## Important
This is a development MVP foundation, not production-ready software. Do not use real customer or banking data. Change development secrets before any shared or deployed environment. Scoring is a demo LogisticRegression on synthetic data plus a separate decision layer (see `backend/app/ml/README.md`); real external integrations are still planned work. The current INN lookup uses seeded mock data; banker workflow is available through the API/Swagger, while a full banker-facing UI remains planned.
