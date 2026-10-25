"""Explicit, auditable application status transitions for the MVP."""
from app.models.models import ApplicationStatus

# A transition is allowed only when it appears in this map. The banker makes
# manual decisions in this demo; scoring itself is intentionally a separate task.
ALLOWED_TRANSITIONS: dict[str, set[str]] = {
    ApplicationStatus.draft.value: {ApplicationStatus.submitted.value},
    ApplicationStatus.submitted.value: {ApplicationStatus.data_check.value},
    ApplicationStatus.data_check.value: {ApplicationStatus.scoring.value},
    ApplicationStatus.scoring.value: {
        ApplicationStatus.approved.value,
        ApplicationStatus.other_terms.value,
        ApplicationStatus.documents_required.value,
        ApplicationStatus.rejected.value,
    },
    ApplicationStatus.approved.value: {ApplicationStatus.signing.value},
    ApplicationStatus.other_terms.value: {ApplicationStatus.signing.value},
    ApplicationStatus.documents_required.value: {ApplicationStatus.scoring.value},
    ApplicationStatus.signing.value: {ApplicationStatus.disbursed.value},
    ApplicationStatus.rejected.value: set(),
    ApplicationStatus.disbursed.value: set(),
}


def validate_transition(current: str, target: str) -> None:
    """Raise ValueError for an unknown or disallowed transition."""
    known = {status.value for status in ApplicationStatus}
    if target not in known:
        raise ValueError(f"Unknown target status: {target}")
    if target not in ALLOWED_TRANSITIONS.get(current, set()):
        raise ValueError(f"Transition {current} -> {target} is not allowed")
