"""Domain model tests (T004): no HTTP, no database."""

from changeflow.domain.model import TRANSITIONS, Role, Status


def test_status_has_exactly_the_workflow_values():
    assert {s.value for s in Status} == {
        "Draft",
        "PendingReview",
        "ChangesRequested",
        "Approved",
    }


def test_role_has_exactly_requester_and_reviewer():
    assert {r.value for r in Role} == {"requester", "reviewer"}


def test_transition_table_is_exactly_the_specified_workflow():
    assert TRANSITIONS == {
        (Status.DRAFT, "edit"): Status.DRAFT,
        (Status.CHANGES_REQUESTED, "edit"): Status.CHANGES_REQUESTED,
        (Status.DRAFT, "submit"): Status.PENDING_REVIEW,
        (Status.CHANGES_REQUESTED, "submit"): Status.PENDING_REVIEW,
        (Status.PENDING_REVIEW, "approve"): Status.APPROVED,
        (Status.PENDING_REVIEW, "request_changes"): Status.CHANGES_REQUESTED,
    }


def test_approved_is_terminal():
    assert not [key for key in TRANSITIONS if key[0] is Status.APPROVED]


def test_there_is_no_delete_operation():
    operations = {operation for _, operation in TRANSITIONS}
    assert operations == {"edit", "submit", "approve", "request_changes"}
    assert "delete" not in operations
