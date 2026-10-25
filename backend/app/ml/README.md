# ML-скоринг (демо)

LogisticRegression (scikit-learn) на **синтетических** данных + отдельный слой бизнес-решений.
Это демонстрация процесса, а не кредитная модель: реальных кредитных историй здесь нет.

## Запуск (из `backend/`)
```bash
pip install -r requirements.txt
python -m app.ml.train            # обучение; пишет app/ml/artifacts/{risk_model.joblib,metrics.json}
python -m app.ml.train --export-csv /tmp/dataset.csv   # + выгрузка датасета
pytest                            # тесты
```
Если артефакта нет или версия sklearn другая, `app/ml/model.py` обучит ту же модель в памяти
(seed фиксирован, ~1 с).

## Данные и метки
5 000 заявок, `numpy.random.default_rng(42)` (`app/ml/data.py`). Метка `high_risk` сэмплируется
из логита с **вручную заданными весами** (`config.LABEL_RULE`): долговая нагрузка, просрочки,
сумма/выручка, возраст компании, выручка + шум. Base rate ≈ 27%.

## Признаки
`company_age_years`, `annual_revenue`, `requested_amount`, `debt_to_revenue`, `overdue_count`
и производный `amount_to_revenue` (= сумма / выручка; без него линейная модель не увидит
«сумма относительно выручки»). Откуда берутся значения в `credit_pipeline.build_features`:

| Признак | Источник в текущей схеме |
|---|---|
| annual_revenue | `Company.revenue` (в коде это годовая выручка) |
| requested_amount | `Application.amount` |
| debt_to_revenue | `Company.debt / Company.revenue` |
| overdue_count | **нет поля** → прокси: 1, если `overdue_days > 0`, иначе 0 |
| company_age_years | **нет поля** → медиана train (отмечается в `assumed_inputs`) |

## Обучение и метрики
Train/test 80/20 (`random_state=42`, stratify), `StandardScaler + LogisticRegression`, обучение
только на train, без подбора гиперпараметров. Тест (1 000 заявок), порог классификации 0.5:

| precision | recall | F1 | ROC-AUC |
|---|---|---|---|
| 0.593 | 0.257 | 0.359 | 0.706 |

Метрики скромные намеренно: метки зашумлены, и они показывают лишь то, насколько модель
восстанавливает нашу же формулу. Низкий recall при отсечке 0.5 — следствие base rate 27%;
решения принимаются по порогам ниже, а не по этой отсечке. Актуальные цифры: `artifacts/metrics.json`.

## Выход модели
`risk_probability` ∈ [0, 1]; `score = round(100 * (1 - p))`; `risk_level` по той же вероятности
(low < 0.25 ≤ medium < 0.50 ≤ high); `top_factors` — вклад признака в вероятность в п.п. относительно
среднего заявителя (в `score_factors` показываются вклады ≥ 2 п.п. как отрицательные «баллы»).

## Слой решений (`decision.py`, пороги в `config.py`)
Порядок: 1) критические факторы → `rejected`; 2) пробелы в данных → `documents_required`;
3) вероятность + продукт. Модель не может одобрить заявку поверх п. 1–2.

| Продукт | approved | other_terms | rejected | Доп. правила |
|---|---|---|---|---|
| credit | p < 0.25 | 0.25 ≤ p < 0.50 | p ≥ 0.50 | — |
| overdraft | p < 0.20 | 0.20 ≤ p < 0.40 | p ≥ 0.40 | авто-одобрение только при долге/выручке ≤ 0.6 и сумме ≤ 25% годовой выручки, иначе `other_terms` |
| working_capital | p < 0.25 | 0.25 ≤ p < 0.50 | p ≥ 0.50 | без выручки → `documents_required` (общее правило) |

Все пороги — **стартовые демо-значения**, не политика банка. Стоп-факторы: статус ЕГРЮЛ/БКИ из
`CRITICAL_STATUSES`, просрочка > 90 дн. Неполные проверки: любой статус, кроме `passed`/`warning`.
`other_terms` → `recommended_amount` = 80% суммы (для овердрафта не выше лимита).

Reason codes (возвращаются только применимые): `EXTERNAL_CHECK_FAILED`, `LONG_OVERDUE`, `MISSING_DOCUMENTS`,
`EXTERNAL_CHECKS_INCOMPLETE`, `MISSING_DATA`, `HIGH/MEDIUM/LOW_RISK_PROBABILITY`, `HIGH_DEBT_RATIO`,
`OVERDUE_HISTORY`, `AMOUNT_TO_REVENUE_HIGH`, `PRODUCT_LIMIT_EXCEEDED`.

## Ограничения
- Синтетические метки: качество на реальных данных неизвестно; калибровка вероятности не проверялась.
- Нет полей возраста компании и счётчика просрочек (см. таблицу), нет модели документов — `missing_documents`
  пока передаётся параметром (по умолчанию `False`).
- Тренд выручки, BKI score, срок кредита, отрасль в модель не входят.
- Решение — рекомендация; окончательное остаётся за банкиром.
