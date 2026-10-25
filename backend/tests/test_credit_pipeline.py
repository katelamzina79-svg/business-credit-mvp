from types import SimpleNamespace

from app.services.external_checks import run_external_checks
from app.services.credit_pipeline import evaluate_application


def make_company(revenue, debt, overdue_days, okved="46.90"):
    return SimpleNamespace(
        inn="7701234567",
        name="ООО Тест",
        okved=okved,
        revenue=revenue,
        debt=debt,
        overdue_days=overdue_days,
    )


def make_application(amount=1_000_000, term_months=12, product="credit"):
    return SimpleNamespace(amount=amount, term_months=term_months, product=product)


def test_low_risk_synthetic_company_recommends_approval():
    company = make_company(revenue=12_000_000, debt=1_500_000, overdue_days=0)
    checks = run_external_checks(company)
    result = evaluate_application(make_application(), company, checks)

    assert checks["egrul"]["status"] == "passed"
    assert checks["bki"]["status"] == "passed"
    assert result["score"] == 100
    assert result["risk_level"] == "low"
    assert result["decision_recommendation"] == "approved"
    assert result["decision_reasons"]


def test_overdue_and_high_debt_company_is_flagged():
    company = make_company(revenue=4_500_000, debt=3_200_000, overdue_days=45, okved="47.11")
    checks = run_external_checks(company)
    result = evaluate_application(make_application(), company, checks)

    assert checks["bki"]["status"] == "warning"
    assert result["score"] < 55
    assert result["risk_level"] == "high"
    assert result["decision_recommendation"] == "rejected"
    assert any(factor["code"] == "bki_overdue_30" for factor in result["score_factors"])


def test_large_amount_requests_additional_information():
    company = make_company(revenue=1_000_000, debt=100_000, overdue_days=0)
    result = evaluate_application(make_application(amount=1_500_000), company, run_external_checks(company))

    assert result["decision_recommendation"] in {"documents_required", "rejected"}
    assert result["decision_reasons"]
