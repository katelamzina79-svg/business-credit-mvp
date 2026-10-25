# Petos — handoff and demo checks

## Implemented feed

The client feed is rule-based and uses the latest application for the authenticated client:
- company OKVED;
- application status;
- score (0 before scoring is available).

Implementation:
- `backend/app/services/smart_feed.py` — suggestion rules;
- `backend/app/api/feed.py` — `GET /api/feed` and authenticated HTML fragment `GET /feed/snippet`;
- `backend/templates/feed_snippet.html` — rendered feed fragment;
- `backend/templates/list.html` — loads the fragment into the client page.

The integration is intentionally deterministic and mock-only. It is not an LLM, does not query live news, EGRUL, or BKI, and must be presented as contextual tips rather than verified external information.

## Postman smoke/E2E collection

Import `postman/Business-Credit-MVP.postman_collection.json` into Postman. Set `baseUrl` if the API is not at `http://localhost:8000`. The collection uses seeded local demo accounts and seeded company INN `7701234567`.

Recommended order:
1. Client login → current user → company lookup → create draft → submit.
2. Repeat “get application” until status is `scoring`; inspect `score`, `risk_level`, `decision_recommendation`, `decision_reasons`, and `external_checks`.
3. Check the personalized feed.
4. Banker login → queue → application detail.
5. Run exactly one banker decision request from the four alternatives.
6. For `approved` or `other_terms`, run client login again and then “sign demo offer”. Do not run signing after `rejected`.

The submit request schedules a FastAPI background task, so scoring is not guaranteed to be complete in the immediate submit response. Poll the application detail manually between requests.

## Demo personas / expected coverage

Use the seeded companies for a quick smoke test:
- INN `7701234567` — `ООО Альфа Трейд`, revenue 12,000,000, debt 1,500,000, overdue 0. Baseline low-risk profile; expected to be more favourable than the second profile, subject to request amount and current scoring rules.
- INN `7707654321` — `ООО Ритейл Плюс`, revenue 4,500,000, debt 3,200,000, overdue 45. Elevated-risk profile with overdue history; current rules are expected to recommend rejection because overdue is at least 30 days.

For the Day 5 checklist, add or retain at least 5–6 synthetic persona tests in `backend/tests/test_credit_pipeline.py`: clean baseline, small overdue, overdue >=30, moderate debt ratio, high debt ratio, requested amount above revenue, and long term. Confirm these are tests of the *agreed* scoring specification, not just hard-coded expectations copied from current implementation.

## Assumptions / limits

- All EGRUL/BKI values are synthetic records in the local database. `external_checks.py` labels sources as `synthetic_registry` and `synthetic_bureau`.
- Feed personalization is rules-based (OKVED/status/score), with no live news API.
- Scoring is a transparent demo scorecard, not a trained or validated production credit-risk model. Gena and the team must agree the feature set, target/outcome assumptions, split/evaluation method, thresholds, and human-review boundary before describing it as ML.
- No real banking, bureau, registry, signing, or disbursement integration is implemented by these mocks.
