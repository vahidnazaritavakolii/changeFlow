"""Shared domain rule tests (T005): visibility, text and version validation.

No HTTP, no database.
"""

import pytest

from changeflow.domain import rules
from changeflow.domain.errors import Conflict, InvalidInput, InvalidStatus
from changeflow.domain.model import Actor, ChangeRequest, Role, Status


def make_request(requester_id="alice", status=Status.DRAFT, version=1):
    return ChangeRequest(
        id=1,
        title="T",
        description="D",
        reason="R",
        requester_id=requester_id,
        status=status,
        version=version,
        changes_requested_reason=None,
    )


def actor(user_id, *roles):
    return Actor(user_id=user_id, roles=frozenset(roles))


# --- Visibility (FR-015) ---------------------------------------------------


@pytest.mark.parametrize(
    "roles",
    [(Role.REQUESTER,), (Role.REVIEWER,), (Role.REQUESTER, Role.REVIEWER), ()],
)
def test_owner_sees_own_request_with_any_roles_or_none(roles):
    assert rules.is_visible(actor("alice", *roles), make_request("alice"))


def test_reviewer_sees_any_request():
    assert rules.is_visible(actor("bob", Role.REVIEWER), make_request("alice"))


def test_requester_only_non_owner_sees_nothing():
    assert not rules.is_visible(actor("carol", Role.REQUESTER), make_request("alice"))


def test_no_role_non_owner_sees_nothing():
    assert not rules.is_visible(actor("dave"), make_request("alice"))


# --- Text validation (FR-004, A6, PA-5) -------------------------------------


def test_limits_are_module_level_constants():
    assert rules.TITLE_MAX == 200
    assert rules.TEXT_MAX == 10_000


def valid_text(**overrides):
    body = {"title": "T", "description": "D", "reason": "R"}
    body.update(overrides)
    return body


def test_text_at_the_limits_is_accepted():
    body = valid_text(title="t" * 200, description="d" * 10_000, reason="r" * 10_000)
    values = rules.validate_text(body, "title", "description", "reason")
    assert values == body


@pytest.mark.parametrize(
    "field,value",
    [("title", "t" * 201), ("description", "d" * 10_001), ("reason", "r" * 10_001)],
)
def test_text_over_the_limit_is_rejected(field, value):
    with pytest.raises(InvalidInput):
        rules.validate_text(valid_text(**{field: value}), "title", "description", "reason")


@pytest.mark.parametrize("field", ["title", "description", "reason"])
@pytest.mark.parametrize("value", ["", "   ", "\t\n"])
def test_blank_text_is_rejected(field, value):
    with pytest.raises(InvalidInput):
        rules.validate_text(valid_text(**{field: value}), "title", "description", "reason")


@pytest.mark.parametrize("field", ["title", "description", "reason"])
def test_missing_text_is_rejected(field):
    body = valid_text()
    del body[field]
    with pytest.raises(InvalidInput):
        rules.validate_text(body, "title", "description", "reason")


@pytest.mark.parametrize("value", [None, 1, True, ["x"], {"x": 1}])
def test_non_string_text_is_rejected(value):
    with pytest.raises(InvalidInput):
        rules.validate_text(valid_text(title=value), "title", "description", "reason")


def test_text_values_are_returned_unchanged_not_trimmed():
    body = valid_text(title="  padded  ")
    assert rules.validate_text(body, "title")["title"] == "  padded  "


# --- Body and version validation ---------------------------------------------


@pytest.mark.parametrize("body", [None, [], "text", 1, object()])
def test_body_that_is_not_a_json_object_is_rejected(body):
    with pytest.raises(InvalidInput):
        rules.validate_body(body)


def test_dict_body_is_accepted():
    assert rules.validate_body({"version": 1}) == {"version": 1}


def test_version_one_is_valid():
    assert rules.validate_version({"version": 1}) == 1


@pytest.mark.parametrize("value", [0, -1, "1", True, 1.0, None])
def test_invalid_version_values_are_rejected(value):
    with pytest.raises(InvalidInput):
        rules.validate_version({"version": value})


def test_missing_version_is_rejected():
    with pytest.raises(InvalidInput):
        rules.validate_version({})


# --- Version and status checks ------------------------------------------------


def test_check_version_accepts_current_version():
    rules.check_version(make_request(version=3), 3)


def test_check_version_rejects_other_version():
    with pytest.raises(Conflict):
        rules.check_version(make_request(version=3), 2)


def test_next_status_follows_transition_table():
    assert rules.next_status(make_request(status=Status.DRAFT), "submit") is Status.PENDING_REVIEW


def test_next_status_rejects_transition_not_in_table():
    with pytest.raises(InvalidStatus):
        rules.next_status(make_request(status=Status.APPROVED), "edit")
