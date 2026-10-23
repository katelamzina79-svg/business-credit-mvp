# Business Credit MVP

MVP for SME business credit applications. This repository contains the backend foundation and analysis/design artifacts prepared for Days 1–2.

## Current status
- FastAPI + PostgreSQL + Docker Compose backend foundation (`backend/`)
- SQLAlchemy models and Alembic initial migration
- JWT authentication with `client` and `banker` roles
- Seed data for local testing
- API contract: `backend/openapi_contract.md`
- Day 1–2 analyst documentation: `docs/`

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
This is a development MVP foundation, not production-ready software. Do not use real customer or banking data. Change development secrets before any shared or deployed environment. The scoring pipeline, external data mocks, full application state machine, and complete UI are still planned work.
