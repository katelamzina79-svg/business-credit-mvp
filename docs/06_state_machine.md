# День 2 — Диаграмма состояний заявки

```mermaid
stateDiagram-v2
    [*] --> DRAFT
    DRAFT --> SUBMITTED: submit
    SUBMITTED --> DATA_CHECK: start_check
    DATA_CHECK --> SCORING: data_ok
    DATA_CHECK --> NEED_DOCUMENTS: missing_data
    DATA_CHECK --> REJECTED: invalid_data/fraud_flag
    NEED_DOCUMENTS --> DATA_CHECK: documents_uploaded
    SCORING --> APPROVED: score >= approve_threshold
    SCORING --> OTHER_TERMS: score in review_band
    SCORING --> NEED_DOCUMENTS: insufficient_information
    SCORING --> REJECTED: score < reject_threshold
    OTHER_TERMS --> SIGNING: client_accepts
    APPROVED --> SIGNING: client_accepts
    SIGNING --> ISSUED: mock_signed
    ISSUED --> [*]
    REJECTED --> [*]

    SCORING --> BANKER_REVIEW: manual_review
    DATA_CHECK --> BANKER_REVIEW: exception
    BANKER_REVIEW --> APPROVED: banker_approve
    BANKER_REVIEW --> OTHER_TERMS: banker_change_terms
    BANKER_REVIEW --> NEED_DOCUMENTS: banker_request_info
    BANKER_REVIEW --> REJECTED: banker_reject
```

## Канонические статусы API
- DRAFT
- SUBMITTED
- DATA_CHECK
- SCORING
- APPROVED
- OTHER_TERMS
- NEED_DOCUMENTS
- REJECTED
- SIGNING
- ISSUED
- BANKER_REVIEW

## Запреты переходов
- DRAFT → SCORING напрямую нельзя.
- REJECTED → APPROVED автоматически нельзя.
- ISSUED → любое другое состояние нельзя.
- Клиент не может менять решение напрямую.
- Банкир не должен вручную менять системные результаты без записи причины в audit log.
