# Аня — День 1 + День 2

Backend foundation for Business Credit MVP.

## День 1
- FastAPI + PostgreSQL + Docker Compose
- проектная структура
- requirements/lock-equivalent через pinned requirements.txt + pyproject.toml
- базовый OpenAPI-контракт
- Jinja2 layout/login/list templates for Катя

## День 2
- SQLAlchemy models
- Alembic initial migration
- CRUD клиентов/компаний/заявок
- JWT authentication
- роли client/banker
- seed data

## Запуск

```bash
docker compose up --build
```

API: http://localhost:8000
Swagger: http://localhost:8000/docs

## Тестовые аккаунты

- client@example.com / client123
- banker@example.com / banker123

## Примечание
Это foundation на конец Дня 2. State machine, внешние моки, scoring pipeline, документы и фоновые задачи — следующие дни.
