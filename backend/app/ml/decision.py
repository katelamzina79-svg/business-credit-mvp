"""Business decision layer. Deliberately separate from the model.

Priority (first match wins):
  1. critical external-check problems / hard stops          -> rejected
  2. missing documents, incomplete checks, missing data     -> documents_required
  3. model probability + product rules                      -> approved / other_terms / rejected
The model can never turn 1 or 2 into an approval.
"""
from app.ml import config as cfg

REASON_TEXT = {
    "EXTERNAL_CHECK_FAILED": "Внешняя проверка (ЕГРЮЛ/БКИ) выявила критическую проблему.",
    "LONG_OVERDUE": "Просрочка по данным БКИ превышает {days} дней (стоп-фактор).",
    "MISSING_DOCUMENTS": "Не хватает обязательных документов.",
    "EXTERNAL_CHECKS_INCOMPLETE": "Внешние проверки ЕГРЮЛ/БКИ не завершены или требуют уточнения.",
    "MISSING_DATA": "Недостаточно данных: не указана выручка компании.",
    "HIGH_RISK_PROBABILITY": "Высокая вероятность условного кредитного риска по демо-модели.",
    "MEDIUM_RISK_PROBABILITY": "Средняя вероятность условного кредитного риска: рассмотреть другие условия.",
    "LOW_RISK_PROBABILITY": "Низкая вероятность условного кредитного риска по демо-модели.",
    "HIGH_DEBT_RATIO": "Долговая нагрузка не ниже 60% годовой выручки.",
    "OVERDUE_HISTORY": "В данных БКИ есть просрочка.",
    "AMOUNT_TO_REVENUE_HIGH": "Запрошенная сумма превышает 50% годовой выручки.",
    "PRODUCT_LIMIT_EXCEEDED": "Сумма выше лимита овердрафта, рассчитанного от выручки.",
}


def reason_text(code: str) -> str:
    return REASON_TEXT[code].format(days=cfg.LONG_OVERDUE_DAYS)


def risk_level(probability: float) -> str:
    t = cfg.RISK_LEVEL_THRESHOLDS
    return "low" if probability < t["approve_below"] else "medium" if probability < t["reject_from"] else "high"


def check_state(external_checks: dict) -> str:
    """'critical' | 'incomplete' | 'ok' for the EGRUL/BKI results."""
    state = "ok"
    for name in cfg.REQUIRED_CHECKS:
        status = ((external_checks or {}).get(name) or {}).get("status")
        if status in cfg.CRITICAL_STATUSES:
            return "critical"
        if status not in cfg.OK_STATUSES:
            state = "incomplete"
    return state


def decide(
    risk_probability: float,
    product: str,
    features: dict,
    external_checks: dict,
    overdue_days: int = 0,
    missing_documents: bool = False,
    missing_data: bool = False,
) -> dict:
    """Return {decision, reason_codes, recommended_amount}. Only applicable reasons are returned."""
    amount = float(features["requested_amount"])
    soft: list[str] = []  # informational codes that apply regardless of the decision
    if features["debt_to_revenue"] >= cfg.HIGH_DEBT_RATIO:
        soft.append("HIGH_DEBT_RATIO")
    if overdue_days > 0 or features["overdue_count"] > 0:
        soft.append("OVERDUE_HISTORY")
    if features["amount_to_revenue"] > cfg.HIGH_AMOUNT_TO_REVENUE:
        soft.append("AMOUNT_TO_REVENUE_HIGH")

    # 1. Critical factors -> rejected, whatever the model says.
    hard: list[str] = []
    if check_state(external_checks) == "critical":
        hard.append("EXTERNAL_CHECK_FAILED")
    if overdue_days > cfg.LONG_OVERDUE_DAYS:
        hard.append("LONG_OVERDUE")
    if hard:
        return _result("rejected", hard + [c for c in soft if c not in hard])

    # 2. Not enough information -> documents_required, whatever the model says.
    gaps: list[str] = []
    if missing_documents:
        gaps.append("MISSING_DOCUMENTS")
    if check_state(external_checks) == "incomplete":
        gaps.append("EXTERNAL_CHECKS_INCOMPLETE")
    if missing_data:
        gaps.append("MISSING_DATA")
    if gaps:
        return _result("documents_required", gaps + soft)

    # 3. Model probability + product rules.
    rules = cfg.PRODUCT_RULES.get(product) or cfg.PRODUCT_RULES[cfg.DEFAULT_PRODUCT]
    if risk_probability >= rules["reject_from"]:
        return _result("rejected", ["HIGH_RISK_PROBABILITY"] + soft)
    if risk_probability >= rules["approve_below"]:
        return _result("other_terms", ["MEDIUM_RISK_PROBABILITY"] + soft, _reduced(amount))

    decision, codes, rec = "approved", ["LOW_RISK_PROBABILITY"] + soft, None
    if product == "overdraft":
        limit = float(features["annual_revenue"]) * rules["limit_share_of_annual_revenue"]
        if features["debt_to_revenue"] > rules["max_debt_to_revenue_for_approval"]:
            decision, rec = "other_terms", _reduced(amount)
            if "HIGH_DEBT_RATIO" not in codes:
                codes.append("HIGH_DEBT_RATIO")
        if amount > limit:
            decision, rec = "other_terms", round(min(limit, _reduced(amount)), 2)
            codes.append("PRODUCT_LIMIT_EXCEEDED")
    if decision == "other_terms":  # probability is low; the product rule is the reason
        codes.remove("LOW_RISK_PROBABILITY")
    return _result(decision, codes, rec)


def _reduced(amount: float) -> float:
    return round(amount * cfg.OTHER_TERMS_AMOUNT_SHARE, 2)


def _result(decision: str, codes: list[str], recommended_amount: float | None = None) -> dict:
    return {
        "decision": decision,
        "reason_codes": list(dict.fromkeys(codes)),
        "recommended_amount": recommended_amount,
    }
