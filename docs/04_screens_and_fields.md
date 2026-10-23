# День 1 — Экраны и поля

## Клиент

### 1. Login
- email/login
- password
- роль определяется аккаунтом

### 2. Dashboard
- имя компании
- активные заявки
- статус каждой заявки
- CTA «Подать заявку»

### 3. Каталог продуктов
Карточки:
- название
- назначение
- ориентировочная сумма
- срок
- краткое описание
- CTA

Продукты MVP:
- Кредит
- Овердрафт
- Оборотный кредит

### 4. Мастер заявки
#### Шаг 1 — продукт
- product_type — required

#### Шаг 2 — компания
- INN — required, 10/12 цифр
- company_name — auto
- legal_form — auto
- registration_date — auto
- OKVED — auto
- region — auto
- company_status — auto

#### Шаг 3 — потребность
- amount — required
- term_months — required
- purpose — required
- expected_monthly_revenue — required

#### Шаг 4 — финансовая информация
- monthly_revenue — auto/manual confirmation
- existing_debt — auto from BKI/mock
- overdue_amount — auto from BKI/mock
- average_balance — synthetic/mock

#### Шаг 5 — подтверждение
- summary
- consent checkbox
- submit

### 5. Страница заявки
- application ID
- product
- amount
- term
- company
- timeline
- current status
- required documents
- decision
- reason codes
- CTA по текущему состоянию

### 6. Подписание
- approved conditions
- repayment summary
- checkbox
- «Подписать» → mock

### 7. Выдача
- status
- amount
- account placeholder
- «Выдано» → mock

## Банкир
### Queue
- application ID
- company
- product
- amount
- score/risk
- status
- created_at
- flag «требует внимания»

### Application review
- company data
- requested conditions
- external checks
- BKI
- scoring score
- risk level
- top factors
- reason codes
- documents
- audit history
- actions: approve / change terms / request info / reject

## Поля, которые не надо спрашивать у клиента на MVP
- название компании, если найдено по ИНН;
- ОКВЭД, если найден;
- дата регистрации;
- юридическая форма;
- базовые данные БКИ;
- результаты внешних проверок.
