# Правила скоринга и решения v2 (ML)

> Синтетическая спецификация для MVP. Не является реальной банковской кредитной политикой.
> Реализация: `backend/app/ml/` и `backend/app/services/credit_pipeline.py`. Подробности: `backend/app/ml/README.md`.
> Числа ниже — стартовые демо-значения; единственное место их изменения — `backend/app/ml/config.py`.

## Что изменилось относительно v1
| Тема | v1 (этот документ раньше) | Код до v2 | v2 (сейчас) |
|---|---|---|---|
| Скоринг | таблица баллов | вычитание баллов | LogisticRegression, `risk_probability` |
| score | старт 100 + бонусы, clamp | 100 − штрафы | `round(100 * (1 − risk_probability))` |
| risk_level | LOW/MEDIUM/HIGH/CRITICAL по score 80/60/40 | low/medium/high по score 75/55 | low/medium/high по вероятности 0.25/0.50 |
| Hard stop по просрочке | > 90 дн. | ≥ 30 дн. | > 90 дн. (как в v1) |
| Продукт | описан, в коде не учитывался | не учитывался | свои пороги и правила (ниже) |
| Статусы | NEED_DOCUMENTS, BANKER_REVIEW | documents_required | documents_required (BANKER_REVIEW в БД нет) |
| Срок кредита | признак | штраф 5 баллов при > 36 мес. | не используется |

## Входные признаки модели
`company_age_years`, `annual_revenue`, `requested_amount`, `debt_to_revenue`, `overdue_count`, `amount_to_revenue` (= сумма / выручка).
Признаки v1, которых в схеме нет или которые не вошли в модель: `revenue_trend`, `bki_score`, `active_loans`,
`company_status`, `overdue_amount`, `requested_term_months`, `monthly_revenue` (в БД выручка годовая).
`company_age_years` и `overdue_count` в схеме отсутствуют: возраст берётся как медиана train, просрочки — прокси `overdue_days > 0`.

## Порядок решения
1. **Критические факторы → `rejected`**: статус ЕГРЮЛ/БКИ из `CRITICAL_STATUSES`; просрочка > 90 дн.
2. **Нехватка информации → `documents_required`**: нет обязательных документов; проверки ЕГРЮЛ/БКИ не завершены
   (любой статус, кроме `passed`/`warning`); нет выручки.
3. **Вероятность + продукт**:

| Продукт | approved | other_terms | rejected |
|---|---|---|---|
| credit | p < 0.25 | 0.25 ≤ p < 0.50 | p ≥ 0.50 |
| overdraft | p < 0.20 | 0.20 ≤ p < 0.40 | p ≥ 0.40 |
| working_capital | p < 0.25 | 0.25 ≤ p < 0.50 | p ≥ 0.50 |

Овердрафт: авто-одобрение только при debt/revenue ≤ 0.6 и сумме ≤ 25% годовой выручки, иначе `other_terms`
(`recommended_amount` не выше лимита). Требование «стабильные обороты» не реализовано: данных об оборотах нет.
Модель не может одобрить заявку поверх п. 1–2.

## Reason codes
Возвращаются только применимые. Для UI хранится текст в `decision_reasons`, коды — в `reason_codes` результата.
- `EXTERNAL_CHECK_FAILED`, `LONG_OVERDUE` — критические (v1: `EXTERNAL_CHECK_ISSUE`, `LONG_OVERDUE`).
- `MISSING_DOCUMENTS`, `EXTERNAL_CHECKS_INCOMPLETE`, `MISSING_DATA`.
- `HIGH_RISK_PROBABILITY` / `MEDIUM_RISK_PROBABILITY` / `LOW_RISK_PROBABILITY` (v1: `LOW_SCORE`).
- `HIGH_DEBT_RATIO` (v1: `HIGH_DEBT_LOAD`), `OVERDUE_HISTORY` (v1: `RECENT_OVERDUE`), `AMOUNT_TO_REVENUE_HIGH`, `PRODUCT_LIMIT_EXCEEDED`.
- `NEW_BUSINESS`, `NEGATIVE_REVENUE_TREND` пока не выдаются: нет данных.

## Важное
Интерфейс и API используют коды/объекты решения, а не hard-coded тексты: пороги меняются в `config.py` без переделки фронта.

---

## Архив: скоринг v1 (балльная таблица, в коде не используется)

> Рабочая синтетическая спецификация для MVP. Не является реальной банковской кредитной политикой.

## Входные признаки
- business_age_months
- monthly_revenue
- revenue_trend
- existing_debt
- overdue_days
- overdue_amount
- bki_score
- active_loans
- company_status
- requested_amount
- requested_term_months
- debt_to_revenue

## Скоринг v1
Начальный score = 100.

| Фактор | Правило | Баллы |
|---|---|---:|
| Компания активна | yes | +10 |
| Возраст бизнеса | >= 24 мес | +15 |
| Возраст бизнеса | 12–23 мес | +10 |
| Возраст бизнеса | 6–11 мес | +5 |
| Возраст бизнеса | < 6 мес | -15 |
| Выручка | стабильный/растущий тренд | +15 |
| Выручка | падающий >20% | -15 |
| Просрочка | 0 дней | +15 |
| Просрочка | 1–30 дней | -15 |
| Просрочка | >30 дней | -35 |
| BKI | >= 700 | +20 |
| BKI | 600–699 | +10 |
| BKI | 500–599 | 0 |
| BKI | <500 | -25 |
| Debt/Revenue | <= 0.3 | +10 |
| Debt/Revenue | 0.3–0.6 | 0 |
| Debt/Revenue | >0.6 | -20 |

Ограничение: итоговый score clamp 0..100.

## Risk level
- 80–100: LOW
- 60–79: MEDIUM
- 40–59: HIGH
- 0–39: CRITICAL

## Решение
1. `score >= 80` и нет hard-stop → APPROVED.
2. `60 <= score < 80` → OTHER_TERMS или BANKER_REVIEW в зависимости от суммы/долговой нагрузки.
3. `40 <= score < 60` → NEED_DOCUMENTS или BANKER_REVIEW.
4. `score < 40` → REJECTED.

## Hard stops
- company_status != ACTIVE → REJECTED.
- overdue_days > 90 → REJECTED.
- критически некорректные данные внешней проверки → BANKER_REVIEW.

## Product rules v1
### Credit
- стандартная сумма/срок;
- при MEDIUM риск — снизить сумму или увеличить контроль документов.

### Overdraft
- требовать стабильные обороты;
- лимит зависит от среднемесячной выручки;
- при сильной долговой нагрузке → OTHER_TERMS/BANKER_REVIEW.

### Working capital
- учитывать выручку и existing_debt;
- при недостаточной информации → NEED_DOCUMENTS.

## Reason codes
- LOW_SCORE — недостаточный итоговый score.
- HIGH_DEBT_LOAD — высокая долговая нагрузка.
- RECENT_OVERDUE — обнаружена недавняя просрочка.
- LONG_OVERDUE — длительная просрочка.
- NEW_BUSINESS — недостаточный возраст бизнеса.
- NEGATIVE_REVENUE_TREND — снижение выручки.
- MISSING_DATA — недостаточно данных.
- EXTERNAL_CHECK_ISSUE — проблема внешней проверки.

## Важное
Гена может изменить числа после согласования. Интерфейс и API должны использовать не hard-coded тексты, а коды/объекты решения, чтобы пороги можно было поменять без переделки фронта.
