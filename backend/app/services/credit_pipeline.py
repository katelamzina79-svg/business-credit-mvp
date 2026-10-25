"""Explainable rule-based scoring and recommendation for the hackathon MVP.

This is a transparent synthetic-data demo, not a production credit model.
The thresholds should be aligned with Gena's scoring specification before demo freeze.
"""
from app.models.models import Application, Company


def evaluate_application(application: Application, company: Company, external_checks: dict) -> dict:
    revenue = float(company.revenue or 0)
    debt = float(company.debt or 0)
    amount = float(application.amount or 0)
    term_months = int(application.term_months or 0)
    overdue_days = int((external_checks.get("bki") or {}).get("overdue_days", 0))

    score = 100
    factors: list[dict] = []
    reasons: list[str] = []

    def penalize(code: str, label: str, points: int, reason: str) -> None:
        nonlocal score
        score -= points
        factors.append({"code": code, "label": label, "impact": -points})
        reasons.append(reason)

    if overdue_days >= 30:
        penalize("bki_overdue_30", "Просрочка 30 дней и более", 45,
                 f"В демонстрационных данных БКИ указана просрочка {overdue_days} дн.")
    elif overdue_days > 0:
        penalize("bki_overdue", "Есть просрочка", 20,
                 f"В демонстрационных данных БКИ указана просрочка {overdue_days} дн.")

    debt_ratio = debt / revenue if revenue > 0 else 1.0
    if debt_ratio >= 0.60:
        penalize("high_debt_ratio", "Высокая долговая нагрузка", 25,
                 "Долг составляет не менее 60% годовой выручки в тестовом профиле.")
    elif debt_ratio >= 0.30:
        penalize("medium_debt_ratio", "Повышенная долговая нагрузка", 15,
                 "Долг составляет не менее 30% годовой выручки в тестовом профиле.")
    elif debt_ratio >= 0.15:
        penalize("debt_ratio", "Умеренная долговая нагрузка", 8,
                 "Долговую нагрузку стоит учесть при проверке заявки.")

    amount_ratio = amount / revenue if revenue > 0 else 2.0
    if amount_ratio > 1:
        penalize("amount_over_revenue", "Сумма выше годовой выручки", 20,
                 "Запрошенная сумма превышает годовую выручку из тестового профиля.")
    elif amount_ratio > 0.5:
        penalize("large_amount", "Высокая сумма относительно выручки", 10,
                 "Запрошенная сумма превышает 50% годовой выручки из тестового профиля.")

    if term_months > 36:
        penalize("long_term", "Длительный срок", 5,
                 "Срок заявки превышает 36 месяцев и требует дополнительной проверки.")

    score = max(0, min(100, score))
    risk_level = "low" if score >= 75 else "medium" if score >= 55 else "high"

    if overdue_days >= 30 or score < 35:
        recommendation = "rejected"
        reasons.insert(0, "Рекомендация демо-правил: отказ из-за критичного фактора риска.")
    elif score < 55 or amount_ratio > 1:
        recommendation = "documents_required"
        reasons.insert(0, "Рекомендация демо-правил: запросить дополнительные сведения.")
    elif score < 75 or amount_ratio > 0.5:
        recommendation = "other_terms"
        reasons.insert(0, "Рекомендация демо-правил: рассмотреть меньшую сумму или другие условия.")
    else:
        recommendation = "approved"
        if not reasons:
            reasons.append("По имеющимся тестовым данным критичных факторов риска не выявлено.")
        reasons.insert(0, "Рекомендация демо-правил: одобрение.")

    recommended_amount = round(amount * 0.8, 2) if recommendation == "other_terms" else None

    return {
        "score": score,
        "risk_level": risk_level,
        "score_factors": factors,
        "decision_recommendation": recommendation,
        "decision_reasons": reasons,
        "recommended_amount": recommended_amount,
        "external_checks": external_checks,
        "bki_overdue_days": overdue_days,
    }
