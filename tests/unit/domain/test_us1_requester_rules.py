"""US1 requester rules (T025): create, edit, submit. No HTTP, no database."""

import pytest

from changeflow.domain import rules
from changeflow.domain.errors import Conflict, Forbidden, InvalidInput, InvalidStatus
from changeflow.domain.model import Actor, ChangeRequest, Role, Status

ALICE = Actor("alice", frozenset({Role.REQUESTER}))
ALICE_NO_ROLE = Actor("alice", frozenset())
ALICE_REVIEWER_ONLY = Actor("alice", frozenset({Role.REVIEWER}))
CAROL = Actor("carol", frozenset({Role.REQUESTER}))
BOB = Actor("bob", frozenset({Role.REVIEWER}))
DAVE = Actor("dave", frozenset())

TEXT = {"title": "New title", "description": "New description", "reason": "New reason"}


def request(status=Status.DRAFT, version=1, requester_id="alice", reason_text=None):
    return ChangeRequest(
        id=7,
        title="T",
        description="D",
        reason="R",
        requester_id=requester_id,
        status=status,
        version=version,
        changes_requested_reason=reason_text,
    )


# --- create (FR-005) ---------------------------------------------------------


def test_requester_creates_draft_owned_by_caller():
    created = rules.create_request(ALICE, dict(TEXT))
    assert created == ChangeRequest(
        id=None,
        title="New title",
        description="New description",
        reason="New reason",
        requester_id="alice",
        status=Status.DRAFT,
        version=1,
        changes_requested_reason=None,
    )


@pytest.mark.parametrize("caller", [BOB, DAVE])
def test_create_without_requester_role_is_forbidden(caller):
    with pytest.raises(Forbidden):
        rules.create_request(caller, dict(TEXT))


def test_create_forbidden_is_reported_before_invalid_input():
    with pytest.raises(Forbidden):
        rules.create_request(BOB, {"title": ""})


def test_create_with_invalid_text_is_invalid_input():
    with pytest.raises(InvalidInput):
        rules.create_request(ALICE, {**TEXT, "title": "   "})


# --- edit and submit on own Draft (FR-006, FR-007) ------------------------------


def test_owner_edits_own_draft():
    edited = rules.edit(ALICE, request(version=3), {**TEXT, "version": 3})
    assert edited.status is Status.DRAFT
    assert (edited.title, edited.description, edited.reason) == (
        "New title",
        "New description",
        "New reason",
    )
    assert edited.requester_id == "alice"


def test_edit_keeps_changes_requested_reason():
    edited = rules.edit(
        ALICE, request(status=Status.CHANGES_REQUESTED, reason_text="why"), {**TEXT, "version": 1}
    )
    assert edited.changes_requested_reason == "why"


def test_owner_submits_own_draft():
    submitted = rules.submit(ALICE, request(version=2), {"version": 2})
    assert submitted.status is Status.PENDING_REVIEW
    assert (submitted.title, submitted.description, submitted.reason) == ("T", "D", "R")


# --- permission (FR-008, FR-019) --------------------------------------------------


@pytest.mark.parametrize(
    "caller",
    [CAROL, ALICE_NO_ROLE, ALICE_REVIEWER_ONLY, BOB],
    ids=["non-owner-requester", "owner-lost-role", "owner-reviewer-only", "reviewer"],
)
def test_edit_and_submit_are_forbidden_for_non_owner_or_owner_without_requester_role(caller):
    with pytest.raises(Forbidden):
        rules.edit(caller, request(), {**TEXT, "version": 1})
    with pytest.raises(Forbidden):
        rules.submit(caller, request(), {"version": 1})


# --- status (FR-006, FR-009) ---------------------------------------------------------


@pytest.mark.parametrize("status", [Status.PENDING_REVIEW, Status.APPROVED])
def test_edit_outside_draft_or_changes_requested_is_invalid_status(status):
    with pytest.raises(InvalidStatus):
        rules.edit(ALICE, request(status=status), {**TEXT, "version": 1})


@pytest.mark.parametrize("status", [Status.PENDING_REVIEW, Status.APPROVED])
def test_submit_outside_draft_or_changes_requested_is_invalid_status(status):
    with pytest.raises(InvalidStatus):
        rules.submit(ALICE, request(status=status), {"version": 1})


# --- input and version (FR-004, FR-014) -------------------------------------------------


def test_edit_with_stale_version_is_conflict():
    with pytest.raises(Conflict):
        rules.edit(ALICE, request(version=2), {**TEXT, "version": 1})


def test_submit_with_stale_version_is_conflict():
    with pytest.raises(Conflict):
        rules.submit(ALICE, request(version=2), {"version": 1})


@pytest.mark.parametrize("body", [{**TEXT}, {"version": 1}, None, []])
def test_edit_with_invalid_body_is_invalid_input(body):
    with pytest.raises(InvalidInput):
        rules.edit(ALICE, request(), body)


def test_submit_without_version_is_invalid_input():
    with pytest.raises(InvalidInput):
        rules.submit(ALICE, request(), {})


def test_unknown_extra_fields_are_ignored():
    edited = rules.edit(ALICE, request(), {**TEXT, "version": 1, "status": "Approved"})
    assert edited.status is Status.DRAFT


# --- check order (FR-020) -----------------------------------------------------------------


def test_forbidden_beats_invalid_input():
    with pytest.raises(Forbidden):
        rules.edit(CAROL, request(), {"title": ""})


def test_invalid_input_beats_conflict():
    with pytest.raises(InvalidInput):
        rules.edit(ALICE, request(version=5), {**TEXT, "title": " ", "version": 1})


def test_conflict_beats_invalid_status():
    with pytest.raises(Conflict):
        rules.submit(ALICE, request(status=Status.APPROVED, version=5), {"version": 1})
