"""Synthetic dataset: features + labels from a documented, hand-set rule.

The labels are NOT real defaults. They are sampled from a logistic rule we wrote
(config.LABEL_RULE), so model metrics only show how well LogisticRegression
recovers that rule.
"""
import numpy as np

from app.ml.config import FEATURES, LABEL_RULE, N_SAMPLES, RANDOM_STATE


def generate_dataset(n: int = N_SAMPLES, seed: int = RANDOM_STATE):
    """Return (X, y): X shape (n, len(FEATURES)) in FEATURES order, y in {0, 1}."""
    rng = np.random.default_rng(seed)
    age = np.clip(rng.gamma(2.0, 3.0, n), 0.25, 30.0)                 # years
    revenue = np.clip(rng.lognormal(np.log(8e6), 0.9, n), 3e5, 1e8)   # per year
    debt_to_revenue = rng.beta(1.6, 3.5, n) * 1.2
    amount_to_revenue = np.clip(rng.lognormal(np.log(0.25), 0.7, n), 0.02, 2.5)
    amount = revenue * amount_to_revenue
    overdue_count = np.clip(rng.poisson(0.6, n), 0, 6)

    r = LABEL_RULE
    z = (
        r["intercept"]
        + r["debt_to_revenue"] * debt_to_revenue
        + r["overdue_count"] * overdue_count
        + r["amount_to_revenue"] * np.minimum(amount_to_revenue, 2.0)
        + r["company_age_years"] * np.minimum(age, 15.0)
        + r["log_revenue"] * np.log(revenue / 8e6)
        + rng.normal(0.0, r["noise_sd"], n)
    )
    high_risk = rng.binomial(1, 1.0 / (1.0 + np.exp(-z)))

    columns = {
        "company_age_years": age,
        "annual_revenue": revenue,
        "requested_amount": amount,
        "debt_to_revenue": debt_to_revenue,
        "overdue_count": overdue_count,
        "amount_to_revenue": amount_to_revenue,
    }
    X = np.column_stack([columns[name] for name in FEATURES])
    return X, high_risk.astype(int)
