# День 2 — Handoff коллегам

## Ане — Backend

### Передать
1. `04_screens_and_fields.md`
2. `05_bpmn.md`
3. `06_state_machine.md`
4. `09_er_review.md`

### Критичные требования
- API должен возвращать данные компании после ввода ИНН.
- Application должна иметь state machine.
- Timeline строится из StatusHistory.
- Решение и reason codes должны быть отдельными структурированными данными.
- Нужны endpoint'ы для client и banker flows.
- Jinja layout + login + list page должны быть готовы к началу Day 3.

## Гене — ML/DS

### Передать
1. `08_scoring_rules.md`
2. `02_jtbd_pains.md`

### Критичные требования
- score 0–100;
- risk level;
- top factors;
- reason codes;
- model_version;
- JSON-контракт результата.

Предлагаемый ответ скоринга:
```json
{
  "score": 82,
  "risk_level": "LOW",
  "factors": [
    {"code": "STABLE_REVENUE", "impact": 15},
    {"code": "GOOD_BKI", "impact": 20}
  ],
  "model_version": "v1"
}
```

## Петосу — интеграции

### Передать
1. `04_screens_and_fields.md`
2. `05_bpmn.md`

### Моки должны поддерживать
- GET/POST по ИНН;
- синтетические данные ЕГРЮЛ/ЕГРИП;
- synthetic business transparency;
- BKI result;
- configurable delay;
- configurable error;
- стабильные тестовые ответы для e2e.

## Критическая точка конца Day 2
Команда должна иметь:
- OpenAPI contract;
- DB model;
- seed;
- mocks;
- screen list;
- field specification;
- BPMN;
- state machine;
- scoring rules;
- user stories.
