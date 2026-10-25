"""ML scoring + separate decision layer for the hackathon MVP.

Flow inside this function (the surrounding order EGRUL -> BKI -> scoring -> decision
-> banker -> client is unchanged):
    external_checks -> features -> LogisticRegression probability (app.ml.model)
    -> decision layer (app.ml.decision) -> the same result dict as before.

This is a demo on synthetic data, not a production credit model. See app/ml/README.md.
"""
from app.ml import config as cfg
from app.ml.decision import check_state, decide, reason_text, risk_level
from app.ml.model import predict
from app.models.models import Application, Company

# Minimum probability points a feature must add to be shown as a scoring factor.
MIN_FACTOR_DELTA = 0.02


def build_features(application: Application, company: Company, overdue_days: int) -> tuple[dict, list[str]]:
    """Map the existing schema to model features. Returns (features, names filled by assumption)."""
    revenue = float(company.revenue or 0)
    debt = float(company.debt or 0)
    amount = float(application.amount or 0)
    assumed: list[str] = []

    if revenue > 0:
        debt_to_revenue, amount_to_revenue = debt / revenue, amount / revenue
    else:  # cannot divide: be conservative; the decision layer asks for data separately
        debt_to_revenue = cfg.WORST_CASE["debt_to_revenue"]
        amount_to_revenue = cfg.WORST_CASE["amount_to_revenue"]
        assumed += ["debt_to_revenue", "amount_to_revenue"]

    features = {
        # Company has no age/registration date yet -> None = median of training data.
        "company_age_years": getattr(company, "company_age_years", None),
        "annual_revenue": revenue if revenue > 0 else None,
        "requested_amount": amount,
        "debt_to_revenue": debt_to_revenue,
        "amount_to_revenue": amount_to_revenue,
        # Only overdue_days exists, not a count: proxy 0 / 1.
        "overdue_count": 1 if overdue_days > 0 else 0,
    }
    return features, assumed


def evaluate_application(
    application: Application,
    company: Company,
    external_checks: dict,
    missing_documents: bool = False,
) -> dict:
    bki = (external_checks or {}).get("bki") or {}
    overdue_days = int(bki.get("overdue_days", company.overdue_days or 0) or 0)
    revenue = float(company.revenue or 0)

    features, assumed = build_features(application, company, overdue_days)
    prediction = predict(features)
    p = prediction["risk_probability"]

    outcome = decide(
        risk_probability=p,
        product=application.product,
        features={**features, "annual_revenue": revenue},
        external_checks=external_checks,
        overdue_days=overdue_days,
        missing_documents=missing_documents,
        missing_data=revenue <= 0,
    )

    factors = [
        {
            "code": f["feature"],
            "label": cfg.FEATURE_LABELS[f["feature"]],
            "impact": -round(100 * f["risk_delta"]),  # points of risk vs an average applicant
        }
        for f in prediction["top_factors"]
        if f["risk_delta"] >= MIN_FACTOR_DELTA and round(100 * f["risk_delta"]) > 0
    ]
    reasons = [reason_text(code) for code in outcome["reason_codes"]]
    reasons.insert(0, f"Вероятность высокого риска по демо-модели: {p:.0%} (синтетические данные).")

    return {
        # fields persisted by the API (unchanged names/types)
        "score": prediction["score"],
        "risk_level": risk_level(p),
        "score_factors": factors,
        "decision_recommendation": outcome["decision"],
        "decision_reasons": reasons,
        "recommended_amount": outcome["recommended_amount"],
        "external_checks": external_checks,
        "bki_overdue_days": overdue_days,
        # extra structured fields (not persisted yet, see README "Open questions")
        "risk_probability": p,
        "reason_codes": outcome["reason_codes"],
        "model_version": prediction["model_version"],
        "assumed_inputs": sorted(set(prediction["imputed_features"]) | set(assumed)),
        "checks_state": check_state(external_checks),
    }
