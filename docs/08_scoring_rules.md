# День 2 — Правила скоринга и решения v1

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
