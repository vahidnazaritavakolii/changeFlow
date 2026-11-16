"""US2 review rules (T031): approve and request changes. No HTTP, no database."""

import pytest

from changeflow.domain import rules
from changeflow.domain.errors import Conflict, Forbidden, InvalidInput, InvalidStatus
from changeflow.domain.model import Actor, ChangeRequest, Role, Status

BOB = Actor("bob", frozenset({Role.REVIEWER}))
CAROL = Actor("carol", frozenset({Role.REQUESTER, Role.REVIEWER}))
ALICE = Actor("alice", frozenset({Role.REQUESTER}))
DAVE = Actor("dave", frozenset())


def request(status=Status.PENDING_REVIEW, version=2, requester_id="alice", reason_text=None):
    return ChangeRequest(
        id=3,
        title="T",
        description="D",
        reason="R",
        requester_id=requester_id,
        status=status,
        version=version,
        changes_requested_reason=reason_text,
    )


def approve(actor, req, **body):
    return rules.approve(actor, req, {"version": req.version, **body})


def request_changes(actor, req, **body):
    return rules.request_changes(actor, req, {"version": req.version, "reason": "Fix", **body})


# --- Allowed (FR-010, FR-011) --------------------------------------------------


@pytest.mark.parametrize("reviewer", [BOB, CAROL], ids=["reviewer", "dual-role-non-owner"])
def test_reviewer_who_is_not_the_requester_approves(reviewer):
    approved = approve(reviewer, request())
    assert approved.status is Status.APPROVED
    assert (approved.title, approved.description, approved.reason) == ("T", "D", "R")


def test_request_changes_sets_status_and_reason():
    returned = request_changes(BOB, request(), reason="Add a rollback plan")
    assert returned.status is Status.CHANGES_REQUESTED
    assert returned.changes_requested_reason == "Add a rollback plan"


def test_request_changes_replaces_earlier_reason():
    returned = request_changes(BOB, request(reason_text="old"), reason="new")
    assert returned.changes_requested_reason == "new"


def test_approve_keeps_changes_requested_reason():
    assert approve(BOB, request(reason_text="old")).changes_requested_reason == "old"


# --- Permission (FR-012, FR-016, FR-019) ---------------------------------------------


@pytest.mark.parametrize("caller", [ALICE, DAVE], ids=["requester-only", "no-role"])
def test_caller_without_reviewer_role_is_forbidden(caller):
    with pytest.raises(Forbidden):
        approve(caller, request(requester_id="erin"))
    with pytest.raises(Forbidden):
        request_changes(caller, request(requester_id="erin"))


def test_dual_role_owner_cannot_approve_own_request():
    with pytest.raises(Forbidden):
        approve(CAROL, request(requester_id="carol"))


def test_dual_role_owner_cannot_request_changes_on_own_request():
    with pytest.raises(Forbidden):
        request_changes(CAROL, request(requester_id="carol"))


def test_reviewer_who_lost_the_role_is_forbidden():
    bob_without_role = Actor("bob", frozenset())
    with pytest.raises(Forbidden):
        approve(bob_without_role, request())


# --- Input (FR-011, A6) ------------------------------------------------------------------


@pytest.mark.parametrize(
    "body",
    [{"version": 2}, {"version": 2, "reason": "  "}, {"version": 2, "reason": "r" * 10_001},
     {"version": 2, "reason": 5}],
    ids=["missing", "blank", "too-long", "not-a-string"],
)
def test_request_changes_requires_valid_reason(body):
    with pytest.raises(InvalidInput):
        rules.request_changes(BOB, request(), body)


def test_request_changes_accepts_reason_at_limit():
    assert request_changes(BOB, request(), reason="r" * 10_000).status is Status.CHANGES_REQUESTED


@pytest.mark.parametrize("body", [{}, {"version": "2"}, None])
def test_approve_requires_valid_version(body):
    with pytest.raises(InvalidInput):
        rules.approve(BOB, request(), body)


# --- Status (FR-003) ------------------------------------------------------------------------


@pytest.mark.parametrize(
    "status", [Status.DRAFT, Status.CHANGES_REQUESTED, Status.APPROVED]
)
def test_review_outside_pending_review_is_invalid_status(status):
    with pytest.raises(InvalidStatus):
        approve(BOB, request(status=status))
    with pytest.raises(InvalidStatus):
        request_changes(BOB, request(status=status))


# --- Version (FR-014) and check order (FR-020) --------------------------------------------


def test_stale_version_is_conflict():
    with pytest.raises(Conflict):
        rules.approve(BOB, request(version=3), {"version": 2})
    with pytest.raises(Conflict):
        rules.request_changes(BOB, request(version=3), {"version": 2, "reason": "x"})


def test_self_approval_with_stale_version_is_forbidden():
    with pytest.raises(Forbidden):
        rules.approve(CAROL, request(requester_id="carol", version=3), {"version": 1})


def test_invalid_reason_beats_conflict():
    with pytest.raises(InvalidInput):
        rules.request_changes(BOB, request(version=3), {"version": 1, "reason": ""})


def test_conflict_beats_invalid_status():
    with pytest.raises(Conflict):
        rules.approve(BOB, request(status=Status.APPROVED, version=3), {"version": 1})
