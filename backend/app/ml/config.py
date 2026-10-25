"""Single place for every tunable number in the ML scoring part.

All values are DEMONSTRATION values for the MVP, not a real credit policy.
"""
from pathlib import Path

MODEL_VERSION = "logreg-synthetic-v1"
RANDOM_STATE = 42
N_SAMPLES = 5_000
TEST_SIZE = 0.2

ARTIFACT_DIR = Path(__file__).parent / "artifacts"
ARTIFACT_PATH = ARTIFACT_DIR / "risk_model.joblib"
METRICS_PATH = ARTIFACT_DIR / "metrics.json"

# Model input. The first five are from the agreed spec; amount_to_revenue is
# derived from requested_amount / annual_revenue (no new API field is needed).
FEATURES = [
    "company_age_years",
    "annual_revenue",
    "requested_amount",
    "debt_to_revenue",
    "overdue_count",
    "amount_to_revenue",
]

FEATURE_LABELS = {
    "company_age_years": "Возраст компании",
    "annual_revenue": "Годовая выручка",
    "requested_amount": "Запрошенная сумма",
    "debt_to_revenue": "Долговая нагрузка",
    "overdue_count": "Просрочки в истории",
    "amount_to_revenue": "Сумма относительно выручки",
}

# Hand-set weights of the latent risk used ONLY to generate synthetic labels.
LABEL_RULE = {
    "intercept": -2.8,
    "debt_to_revenue": 3.2,
    "overdue_count": 0.7,
    "amount_to_revenue": 1.6,      # applied to min(amount_to_revenue, 2.0)
    "company_age_years": -0.10,    # applied to min(age, 15)
    "log_revenue": -0.20,          # applied to ln(annual_revenue / 8e6)
    "noise_sd": 0.5,
}

# Used when revenue is missing/zero: conservative values instead of dividing by zero.
WORST_CASE = {"debt_to_revenue": 1.2, "amount_to_revenue": 2.5}

# --- Decision layer -------------------------------------------------------
# Default (credit) probability thresholds; also used for risk_level.
RISK_LEVEL_THRESHOLDS = {"approve_below": 0.25, "reject_from": 0.50}

PRODUCT_RULES = {
    "credit": {"approve_below": 0.25, "reject_from": 0.50},
    # Stricter: overdraft is short, revolving and revenue-bound.
    "overdraft": {
        "approve_below": 0.20,
        "reject_from": 0.40,
        "max_debt_to_revenue_for_approval": 0.60,
        "limit_share_of_annual_revenue": 0.25,
    },
    "working_capital": {"approve_below": 0.25, "reject_from": 0.50},
}
DEFAULT_PRODUCT = "credit"

OTHER_TERMS_AMOUNT_SHARE = 0.8      # recommended_amount = 80% of requested

# Thresholds for human-readable reason codes (independent of the model output).
HIGH_DEBT_RATIO = 0.60
HIGH_AMOUNT_TO_REVENUE = 0.50
LONG_OVERDUE_DAYS = 90              # hard stop, as in docs/08 (overdue_days > 90)

# External check statuses.
OK_STATUSES = {"passed", "warning"}
CRITICAL_STATUSES = {"failed", "not_found", "inactive", "liquidated", "rejected"}
# Any other status (pending, error, timeout, missing entry) = checks incomplete.
REQUIRED_CHECKS = ("egrul", "bki")
