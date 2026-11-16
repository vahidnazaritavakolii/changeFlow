"""US4 rework rules (T039): correct a returned request and resubmit. No HTTP, no DB.

The Domain leaves `version` unchanged; storage increments it on save (research R2). The
version increment for these steps is asserted over HTTP in tests/api/test_us4_rework.py.
"""

from dataclasses import replace

import pytest

from changeflow.domain import rules
from changeflow.domain.errors import Forbidden
from changeflow.domain.model import Actor, ChangeRequest, Role, Status

ALICE = Actor("alice", frozenset({Role.REQUESTER}))
CAROL = Actor("carol", frozenset({Role.REQUESTER}))
BOB = Actor("bob", frozenset({Role.REVIEWER}))

TEXT = {"title": "Corrected", "description": "With rollback plan", "reason": "Audit"}


def returned_request(version=3):
    return ChangeRequest(
        id=5,
        title="T",
        description="D",
        reason="R",
        requester_id="alice",
        status=Status.CHANGES_REQUESTED,
        version=version,
        changes_requested_reason="Add a rollback plan",
    )


def test_owner_edits_returned_request_and_keeps_reason():
    edited = rules.edit(ALICE, returned_request(), {**TEXT, "version": 3})
    assert edited.status is Status.CHANGES_REQUESTED
    assert (edited.title, edited.description, edited.reason) == (
        "Corrected",
        "With rollback plan",
        "Audit",
    )
    assert edited.changes_requested_reason == "Add a rollback plan"


def test_owner_resubmits_returned_request_and_keeps_reason():
    submitted = rules.submit(ALICE, returned_request(), {"version": 3})
    assert submitted.status is Status.PENDING_REVIEW
    assert submitted.changes_requested_reason == "Add a rollback plan"


@pytest.mark.parametrize("caller", [CAROL, BOB], ids=["other-requester", "reviewer"])
def test_non_owner_cannot_edit_or_resubmit(caller):
    with pytest.raises(Forbidden):
        rules.edit(caller, returned_request(), {**TEXT, "version": 3})
    with pytest.raises(Forbidden):
        rules.submit(caller, returned_request(), {"version": 3})


def saved(request):
    """Simulate storage: a successful save increments the version."""
    return replace(request, version=request.version + 1)


def test_full_cycle_until_approval_using_only_domain_rules():
    draft = rules.create_request(ALICE, dict(TEXT))
    draft = replace(draft, id=1)
    assert draft.status is Status.DRAFT

    pending = saved(rules.submit(ALICE, draft, {"version": draft.version}))
    assert pending.status is Status.PENDING_REVIEW

    returned = saved(
        rules.request_changes(BOB, pending, {"version": pending.version, "reason": "Add tests"})
    )
    assert returned.status is Status.CHANGES_REQUESTED

    corrected = saved(rules.edit(ALICE, returned, {**TEXT, "title": "v2",
                                                   "version": returned.version}))
    assert (corrected.status, corrected.title) == (Status.CHANGES_REQUESTED, "v2")

    resubmitted = saved(rules.submit(ALICE, corrected, {"version": corrected.version}))
    assert resubmitted.status is Status.PENDING_REVIEW

    approved = saved(rules.approve(BOB, resubmitted, {"version": resubmitted.version}))
    assert approved.status is Status.APPROVED
    assert approved.version == 6
    assert approved.changes_requested_reason == "Add tests"
