import pytest
from app.models.models import ApplicationStatus
from app.services.workflow import validate_transition


def test_valid_happy_path_transitions():
    validate_transition(ApplicationStatus.draft.value, ApplicationStatus.submitted.value)
    validate_transition(ApplicationStatus.submitted.value, ApplicationStatus.data_check.value)
    validate_transition(ApplicationStatus.data_check.value, ApplicationStatus.scoring.value)
    validate_transition(ApplicationStatus.scoring.value, ApplicationStatus.approved.value)
    validate_transition(ApplicationStatus.approved.value, ApplicationStatus.signing.value)
    validate_transition(ApplicationStatus.signing.value, ApplicationStatus.disbursed.value)


def test_disallowed_transition_is_rejected():
    with pytest.raises(ValueError, match="not allowed"):
        validate_transition(ApplicationStatus.draft.value, ApplicationStatus.approved.value)


def test_rejected_is_terminal():
    with pytest.raises(ValueError, match="not allowed"):
        validate_transition(ApplicationStatus.rejected.value, ApplicationStatus.signing.value)


def test_unknown_target_is_rejected():
    with pytest.raises(ValueError, match="Unknown target status"):
        validate_transition(ApplicationStatus.draft.value, "something_else")
