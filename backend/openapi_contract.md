# OpenAPI contract — Day 1/2

Основные endpoints:

- `POST /api/auth/register` — регистрация пользователя.
- `POST /api/auth/login` — OAuth2 form login, JWT.
- `GET /api/auth/me` — текущий пользователь.
- `GET /api/companies` — список компаний.
- `POST /api/companies` — создать компанию.
- `GET /api/companies/{id}` — компания.
- `GET /api/applications` — заявки текущего клиента / все для банкира.
- `POST /api/applications` — создать черновик.
- `GET /api/applications/{id}` — карточка заявки.
- `POST /api/applications/{id}/submit` — отправить заявку.
- `GET /api/applications/banker/queue` — очередь банкира.
- `GET /health` — healthcheck.

Swagger после запуска: `/docs`; ReDoc: `/redoc`.
