"""Deterministic mock integrations for EGRUL and BKI.

All values come from the synthetic Company registry; no real external data is queried.
"""
from app.models.models import Company


def run_external_checks(company: Company) -> dict:
    """Return stable demo results for the company registry and credit bureau."""
    if not company:
        raise ValueError("Company is required for external checks")

    overdue_days = int(company.overdue_days or 0)
    debt = float(company.debt or 0)

    return {
        "egrul": {
            "status": "passed",
            "source": "synthetic_registry",
            "inn": company.inn,
            "company_name": company.name,
            "okved": company.okved,
        },
        "bki": {
            "status": "warning" if overdue_days > 0 else "passed",
            "source": "synthetic_bureau",
            "debt": debt,
            "overdue_days": overdue_days,
        },
    }
