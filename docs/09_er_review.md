# День 2 — ER-модель: требования Кати к backend

## Минимальные сущности

### User
- id
- email
- password_hash
- role: client/banker
- created_at

### Company
- id
- inn
- name
- legal_form
- registration_date
- okved
- region
- status
- created_at

### Application
- id
- user_id
- company_id
- product_type
- amount
- term_months
- purpose
- status
- created_at
- updated_at

### FinancialSnapshot
- id
- application_id
- monthly_revenue
- revenue_trend
- existing_debt
- overdue_amount
- overdue_days
- average_balance
- created_at

### ExternalCheck
- id
- application_id
- provider
- status
- payload_json
- error_code
- created_at

### ScoringResult
- id
- application_id
- score
- risk_level
- factors_json
- model_version
- created_at

### Decision
- id
- application_id
- decision_type
- approved_amount
- approved_term_months
- reason_codes_json
- decided_by
- created_at

### Document
- id
- application_id
- type
- status
- file_path
- uploaded_by
- created_at

### StatusHistory
- id
- application_id
- from_status
- to_status
- changed_by
- reason
- created_at

### AuditLog
- id
- application_id
- actor_id
- action
- payload_json
- created_at

## Связи
```text
User 1---N Application
Company 1---N Application
Application 1---N FinancialSnapshot
Application 1---N ExternalCheck
Application 1---N ScoringResult
Application 1---N Decision
Application 1---N Document
Application 1---N StatusHistory
Application 1---N AuditLog
```

## Обязательные backend-требования
- INN unique в Company.
- Application status меняется только через state machine.
- История статусов append-only.
- Decision хранит автора: SYSTEM или BANKER.
- ScoringResult versioned.
- ExternalCheck хранит сырой синтетический результат для демонстрации.
