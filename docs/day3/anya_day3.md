# День 3 — Аня: API workflow, статусы и история

## Что реализовано

- Явная таблица разрешённых переходов в `backend/app/services/workflow.py`.
- `POST /api/applications/{id}/submit`: перевод только из `draft` в `submitted`.
- `POST /api/applications/{id}/transition`: ручной переход сотрудником банка с проверкой допустимости.
- `GET /api/applications/{id}/history`: история переходов с датами.
- Каждое изменение статуса записывается в `status_history` и `audit_logs`.
- Проверка доступа: клиент видит только собственные заявки; переходы доступны только роли `banker`.
- Фикс порядка маршрутов: `/banker/queue` объявлен до `/{application_id}`, чтобы не перехватываться динамическим маршрутом.
- Мок-lookup компании по ИНН: `GET /api/companies/lookup/{inn}`.
- Unit-тесты разрешённых и запрещённых переходов.

## Матрица переходов

| Текущий статус | Разрешённый следующий статус |
|---|---|
| `draft` | `submitted` |
| `submitted` | `data_check` |
| `data_check` | `scoring` |
| `scoring` | `approved`, `other_terms`, `documents_required`, `rejected` |
| `documents_required` | `submitted` |
| `approved`, `other_terms` | `signing` |
| `signing` | `disbursed` |
| `rejected`, `disbursed` | переходов нет |

## Быстрая проверка через Swagger

1. Открыть `http://localhost:8000/docs`.
2. Выполнить `POST /api/auth/login` под `banker@example.com` / `banker123` и авторизоваться полученным bearer token.
3. Получить заявку через `GET /api/applications/banker/queue`.
4. Для заявки отправить `POST /api/applications/{id}/transition` с телом `{"target_status":"data_check","comment":"Начата проверка"}`.
5. Повторить переход в `scoring`, затем в один из исходов.
6. Проверить `GET /api/applications/{id}/history`.
7. Попробовать запрещённый переход, например из `draft` сразу в `approved`: ожидается `409 Conflict`.

## Важно

- Скоринг не реализован в этой ветке как ML-модель: переход в `scoring` — статус процесса. Факторы и итоговый расчёт делает Гена отдельным модулем.
- Комментарий перехода в текущей версии хранится как audit action, так как отдельная таблица решений/комментариев потребовала бы миграции. Перед расширением истории стоит добавить отдельную сущность решения.
- Не запускать `alembic revision --autogenerate` только ради этих изменений: используемые таблицы уже присутствуют в стартовой миграции.
