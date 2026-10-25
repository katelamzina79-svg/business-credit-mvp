"""Synthetic-profile tests for ML scoring + the separate decision layer.

Model-dependent tests use inequalities/sets (the model is trained on synthetic data);
decision-layer tests use fixed probabilities and are exact.
"""
import copy
from types import SimpleNamespace

import numpy as np

from app.ml import config as cfg
from app.ml.decision import decide
from app.ml.model import get_artifact, predict
from app.ml.train import train_model
from app.services.credit_pipeline import evaluate_application

OK_CHECKS = {"egrul": {"status": "passed"}, "bki": {"status": "passed", "overdue_days": 0}}


def company(revenue=12_000_000, debt=1_500_000, overdue_days=0):
    return SimpleNamespace(revenue=revenue, debt=debt, overdue_days=overdue_days)


def application(amount=1_000_000, product="credit", term_months=12):
    return SimpleNamespace(amount=amount, product=product, term_months=term_months)


def checks(overdue_days=0, **overrides):
    result = copy.deepcopy(OK_CHECKS)
    result["bki"]["overdue_days"] = overdue_days
    result["bki"]["status"] = "warning" if overdue_days else "passed"
    for name, status in overrides.items():
        result[name]["status"] = status
    return result


def run(c=None, a=None, ch=None, **kwargs):
    c, a = c or company(), a or application()
    return evaluate_application(a, c, ch or checks(c.overdue_days), **kwargs)


# ---- 6 synthetic profiles -------------------------------------------------

def test_profile_low_risk_is_approved():
    r = run()
    assert r["risk_probability"] < 0.25 and r["score"] >= 75
    assert r["decision_recommendation"] == "approved"
    assert r["reason_codes"] == ["LOW_RISK_PROBABILITY"]
    assert r["risk_level"] == "low" and r["recommended_amount"] is None


def test_profile_high_debt_load():
    r = run(company(revenue=5_000_000, debt=4_000_000))
    assert r["risk_probability"] > run()["risk_probability"]
    assert r["decision_recommendation"] in {"other_terms", "rejected"}
    assert "HIGH_DEBT_RATIO" in r["reason_codes"]
    assert r["score_factors"][0]["code"] == "debt_to_revenue"  # biggest contributor first


def test_profile_overdue_history():
    r = run(company(overdue_days=20))
    assert r["risk_probability"] > run()["risk_probability"]
    assert "OVERDUE_HISTORY" in r["reason_codes"] and r["bki_overdue_days"] == 20


def test_profile_amount_above_revenue():
    r = run(company(revenue=1_000_000, debt=100_000), application(amount=1_500_000))
    assert r["decision_recommendation"] in {"other_terms", "rejected"}
    assert "AMOUNT_TO_REVENUE_HIGH" in r["reason_codes"]
    assert r["score_factors"][0]["code"] == "amount_to_revenue"


def test_profile_missing_documents_overrides_low_probability():
    r = run(missing_documents=True)
    assert r["risk_probability"] < 0.25            # the model alone would approve
    assert r["decision_recommendation"] == "documents_required"
    assert "MISSING_DOCUMENTS" in r["reason_codes"]


def test_profile_incomplete_external_checks_overrides_low_probability():
    r = run(ch=checks(bki="pending"))
    assert r["risk_probability"] < 0.25
    assert r["decision_recommendation"] == "documents_required"
    assert "EXTERNAL_CHECKS_INCOMPLETE" in r["reason_codes"]


# ---- critical factors are separate from the model -------------------------

def test_failed_external_check_rejects_even_with_low_probability():
    r = run(ch=checks(egrul="failed"))
    assert r["risk_probability"] < 0.25
    assert r["decision_recommendation"] == "rejected"
    assert r["reason_codes"][0] == "EXTERNAL_CHECK_FAILED"


def test_long_overdue_is_a_hard_stop():
    r = run(company(overdue_days=120))
    assert r["decision_recommendation"] == "rejected" and r["reason_codes"][0] == "LONG_OVERDUE"


def test_missing_revenue_requests_data():
    r = run(company(revenue=0, debt=0))
    assert r["decision_recommendation"] == "documents_required"
    assert "MISSING_DATA" in r["reason_codes"]
    assert "debt_to_revenue" in r["assumed_inputs"]


# ---- decision layer: exact thresholds and product rules -------------------

FEATURES = {"annual_revenue": 10_000_000, "requested_amount": 1_000_000, "debt_to_revenue": 0.2,
            "overdue_count": 0, "amount_to_revenue": 0.1}


def decision(p, product="credit", features=None, ch=None, **kw):
    return decide(p, product, features or FEATURES, ch or OK_CHECKS, **kw)


def test_credit_threshold_boundaries():
    assert decision(0.249)["decision"] == "approved"
    assert decision(0.25)["decision"] == "other_terms"
    assert decision(0.499)["decision"] == "other_terms"
    assert decision(0.50)["decision"] == "rejected"


def test_other_terms_recommends_smaller_amount():
    assert decision(0.3)["recommended_amount"] == 800_000


def test_overdraft_is_stricter_than_credit():
    assert decision(0.22, "credit")["decision"] == "approved"
    assert decision(0.22, "overdraft")["decision"] == "other_terms"
    assert decision(0.45, "credit")["decision"] == "other_terms"
    assert decision(0.45, "overdraft")["decision"] == "rejected"


def test_overdraft_limit_and_debt_cap_block_auto_approval():
    big = decision(0.05, "overdraft", {**FEATURES, "requested_amount": 4_000_000, "amount_to_revenue": 0.4})
    assert big["decision"] == "other_terms" and "PRODUCT_LIMIT_EXCEEDED" in big["reason_codes"]
    assert big["recommended_amount"] <= 10_000_000 * cfg.PRODUCT_RULES["overdraft"]["limit_share_of_annual_revenue"]
    indebted = decision(0.05, "overdraft", {**FEATURES, "debt_to_revenue": 0.7})
    assert indebted["decision"] == "other_terms" and "HIGH_DEBT_RATIO" in indebted["reason_codes"]
    assert decision(0.05, "credit", {**FEATURES, "debt_to_revenue": 0.7})["decision"] == "approved"


def test_gates_beat_probability():
    assert decision(0.01, missing_documents=True)["decision"] == "documents_required"
    assert decision(0.01, overdue_days=91)["decision"] == "rejected"
    failed = {"egrul": {"status": "failed"}, "bki": {"status": "passed"}}
    assert decision(0.01, ch=failed)["decision"] == "rejected"
    # critical beats incomplete
    assert decision(0.01, ch={"egrul": {"status": "failed"}}, missing_documents=True)["decision"] == "rejected"


# ---- model ------------------------------------------------------------------

def test_training_is_reproducible():
    a, b = train_model(), train_model()
    assert np.array_equal(a["pipeline"][-1].coef_, b["pipeline"][-1].coef_)
    assert a["metrics"] == b["metrics"]


def test_metrics_are_honest_and_on_test_split():
    m = get_artifact()["metrics"]
    assert (m["split"]["n_train"], m["split"]["n_test"]) == (4000, 1000)
    assert 0.65 < m["test"]["roc_auc"] < 0.99      # learns the rule, but labels are noisy
    assert set(m["test"]) >= {"precision", "recall", "f1", "roc_auc"}


def test_predict_contract_and_monotonic_risk():
    base = {"company_age_years": 5, "annual_revenue": 8e6, "requested_amount": 2e6,
            "debt_to_revenue": 0.2, "overdue_count": 0, "amount_to_revenue": 0.25}
    low, high = predict(base), predict({**base, "debt_to_revenue": 0.9})
    assert 0 <= low["risk_probability"] <= 1 and low["score"] == round(100 * (1 - low["risk_probability"]))
    assert high["risk_probability"] > low["risk_probability"]
    assert predict({**base, "company_age_years": None})["imputed_features"] == ["company_age_years"]
