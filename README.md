# Business Credit MVP

A demo web application for SME financing: business owners can submit credit applications and track their progress, while bank staff review applications and make decisions through a separate workspace.

> **Status: educational/demo MVP.** This project demonstrates an application workflow and a synthetic-data scoring pipeline. It is not a real lending service and must not be used to make real credit decisions.

## What it does

### Client workspace
- Sign in and navigate separate client pages.
- Create an application for a **business loan**, **overdraft**, or **working-capital financing**.
- Look up a company by INN using a seeded mock registry.
- Submit a requested amount, term, and financing purpose.
- View application statuses and status history; refresh the list or an individual application.
- View demo business tips based on project rules.

### Banker workspace
- Review the application queue and summary counters.
- Inspect mock external-check results, scoring factors, and decision reasons.
- Retry the demo verification pipeline for applications that are still in the submitted/data-check stage.
- Choose a decision for applications at the scoring stage: approve, offer different terms, request documents, or reject.
- Return an application for scoring after documents are marked as received.
- Mark the demo signing/issuance step as complete where the workflow allows it.

### Workflow and scoring
- API-backed application lifecycle with validated status transitions, status history, and audit events.
- JWT-based authentication and role-specific client/banker access.
- Logistic Regression trained on **synthetic data**, with a separate rule-based decision layer.
- A recommendation and contributing factors are shown to support the demo review process; the final decision remains with the banker.

## Tech stack

- **Backend:** Python, FastAPI, SQLAlchemy, Alembic
- **Database:** PostgreSQL
- **Frontend:** server-rendered Jinja2 templates, HTML, Tailwind utility classes and JavaScript
- **ML demo:** scikit-learn Logistic Regression
- **Local environment:** Docker Compose

## Run locally

Requirements: Docker and Docker Compose.

From the repository root:

```bash
cd backend
docker compose up --build
```

The Compose setup starts PostgreSQL, applies Alembic migrations, seeds demo data, and starts the API.

Open:
- Web app: http://localhost:8000
- Interactive API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

### Demo accounts

For local demo use only:

| Role | Email | Password |
|---|---|---|
| Client | `client@example.com` | `client123` |
| Banker | `banker@example.com` | `banker123` |

If the page does not load after startup, check the service status and logs:

```bash
docker compose ps
docker compose logs -f api
```

To stop the services, run `docker compose down` from `backend/`. To also remove the local database volume and its data, use `docker compose down -v`.

## Repository layout

```text
backend/
  app/                 FastAPI application, data models, workflow and ML demo
  templates/            Client, banker and shared page templates
  docker-compose.yml    Local API + PostgreSQL environment
  openapi_contract.md   API contract
docs/                   Analyst/design documentation
docs/day3/              Demo and handoff materials
```

## ML demo: important limitations

The scoring model is deliberately a demonstration, not a validated credit-risk model:
- It is trained on generated synthetic data, not real borrower or credit-bureau records.
- Its labels are generated from manually specified rules, so the metrics only measure how well the model recovers those synthetic rules.
- Some fields are represented by proxies or assumptions because the current schema does not contain all real-world inputs.
- Decision thresholds are starter demo values, not a bank's approved credit policy.
- External checks and company lookup are mocked; real integrations are not configured.

See [the ML README](backend/app/ml/README.md) for features, demo metrics, decision thresholds, and limitations.

## Testing

Run the project's tests from `backend/` in the configured Python environment:

```bash
python -m pytest -q
```

The tests should be run locally before relying on changes; this README update does not imply that the full test suite has passed.

## Security note

This repository is for local development and demonstrations only. Do not enter real customer, company, banking, or other sensitive data. The Compose file contains development credentials and a development JWT secret; replace them and review authentication, authorization, logging, deployment, and data protection before any shared or production deployment.
