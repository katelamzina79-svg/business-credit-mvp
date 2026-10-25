from types import SimpleNamespace

from app.services.credit_pipeline import evaluate_application
from app.services.external_checks import run_external_checks

REQUIRED_KEYS = {
    "score", "risk_level", "score_factors", "decision_recommendation", "decision_reasons",
    "recommended_amount", "external_checks", "bki_overdue_days",
}


def make_company(revenue, debt, overdue_days, okved="46.90"):
    return SimpleNamespace(inn="7701234567", name="ООО Тест", okved=okved,
                           revenue=revenue, debt=debt, overdue_days=overdue_days)


def make_application(amount=1_000_000, term_months=12, product="credit"):
    return SimpleNamespace(amount=amount, term_months=term_months, product=product)


def test_pipeline_keeps_api_contract_for_seeded_low_risk_company():
    company = make_company(revenue=12_000_000, debt=1_500_000, overdue_days=0)
    checks = run_external_checks(company)
    result = evaluate_application(make_application(), company, checks)

    assert checks["egrul"]["status"] == "passed" and checks["bki"]["status"] == "passed"
    assert REQUIRED_KEYS <= result.keys()
    assert 0 <= result["score"] <= 100 and result["risk_level"] == "low"
    assert result["decision_recommendation"] == "approved"
    assert result["decision_reasons"] and result["model_version"]


def test_seeded_overdue_and_high_debt_company_is_not_approved():
    company = make_company(revenue=4_500_000, debt=3_200_000, overdue_days=45, okved="47.11")
    checks = run_external_checks(company)
    result = evaluate_application(make_application(), company, checks)

    assert checks["bki"]["status"] == "warning"
    assert result["decision_recommendation"] in {"other_terms", "rejected"}
    assert result["risk_level"] in {"medium", "high"}
    assert {"HIGH_DEBT_RATIO", "OVERDUE_HISTORY"} <= set(result["reason_codes"])


def test_large_amount_is_not_approved():
    company = make_company(revenue=1_000_000, debt=100_000, overdue_days=0)
    result = evaluate_application(make_application(amount=1_500_000), company, run_external_checks(company))
    assert result["decision_recommendation"] != "approved" and result["decision_reasons"]
