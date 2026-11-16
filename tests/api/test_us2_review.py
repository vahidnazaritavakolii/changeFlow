"""US2 over HTTP (T032): approve and request changes; no self-review.

Requests are created with insert_request, so this story does not depend on US1
endpoints. Every rejection checks the stored row (SC-003).
"""

import pytest


def assert_error(response, status, code):
    assert response.status_code == status, response.text
    assert response.json()["error"]["code"] == code


def approve(client, auth, user, request_id, version):
    return client.post(
        f"/change-requests/{request_id}/approve", json={"version": version}, headers=auth(user)
    )


def request_changes(client, auth, user, request_id, version, reason="Add a rollback plan"):
    body = {"version": version} if reason is None else {"version": version, "reason": reason}
    return client.post(
        f"/change-requests/{request_id}/request-changes", json=body, headers=auth(user)
    )


def assert_rejected(response, status, code, read_row, request_id, before):
    assert_error(response, status, code)
    assert read_row(request_id) == before


# --- Scenario 1: approve -------------------------------------------------------------


def test_reviewer_approves_pending_request(client, auth, insert_request, read_row):
    request_id = insert_request("alice", status="PendingReview", version=2)
    response = approve(client, auth, "bob", request_id, 2)
    assert response.status_code == 200
    assert (response.json()["status"], response.json()["version"]) == ("Approved", 3)
    row = read_row(request_id)
    assert (row["status"], row["version"]) == ("Approved", 3)


# --- Scenario 2: request changes ------------------------------------------------------


def test_reviewer_requests_changes_and_requester_sees_reason(client, auth, insert_request,
                                                             read_row):
    request_id = insert_request("alice", status="PendingReview", version=2)
    response = request_changes(client, auth, "bob", request_id, 2, reason="Add a rollback plan")
    assert response.status_code == 200
    row = read_row(request_id)
    assert (row["status"], row["version"], row["changes_requested_reason"]) == (
        "ChangesRequested",
        3,
        "Add a rollback plan",
    )
    seen = client.get(f"/change-requests/{request_id}", headers=auth("alice")).json()
    assert seen["changes_requested_reason"] == "Add a rollback plan"


# --- Scenarios 3 and 7: no self-review (SC-001) ------------------------------------------


def test_dual_role_owner_cannot_approve_own_request(client, auth, insert_request, read_row):
    request_id = insert_request("carol", status="PendingReview", version=2)
    before = read_row(request_id)
    assert_rejected(approve(client, auth, "carol", request_id, 2),
                    403, "forbidden", read_row, request_id, before)
    assert read_row(request_id)["status"] == "PendingReview"


def test_dual_role_owner_cannot_request_changes_on_own_request(client, auth, insert_request,
                                                               read_row):
    request_id = insert_request("carol", status="PendingReview", version=2)
    before = read_row(request_id)
    assert_rejected(request_changes(client, auth, "carol", request_id, 2),
                    403, "forbidden", read_row, request_id, before)
    assert read_row(request_id)["status"] == "PendingReview"


def test_self_approval_with_outdated_version_is_forbidden(client, auth, insert_request,
                                                          read_row):
    request_id = insert_request("carol", status="PendingReview", version=3)
    before = read_row(request_id)
    assert_rejected(approve(client, auth, "carol", request_id, 1),
                    403, "forbidden", read_row, request_id, before)


# --- Scenario 4: caller without the Reviewer role ------------------------------------------


def test_requester_without_reviewer_role_cannot_review_own_request(client, auth,
                                                                   insert_request, read_row):
    request_id = insert_request("alice", status="PendingReview", version=2)
    before = read_row(request_id)
    assert_rejected(approve(client, auth, "alice", request_id, 2),
                    403, "forbidden", read_row, request_id, before)
    assert_rejected(request_changes(client, auth, "alice", request_id, 2),
                    403, "forbidden", read_row, request_id, before)


def test_user_who_cannot_see_the_request_gets_not_found(client, auth, insert_request,
                                                        read_row):
    request_id = insert_request("alice", status="PendingReview", version=2)
    before = read_row(request_id)
    assert_rejected(approve(client, auth, "dave", request_id, 2),
                    404, "not_found", read_row, request_id, before)
    assert_rejected(request_changes(client, auth, "dave", request_id, 2),
                    404, "not_found", read_row, request_id, before)


# --- Scenario 5: wrong status ---------------------------------------------------------------


@pytest.mark.parametrize("status", ["Draft", "ChangesRequested", "Approved"])
def test_review_outside_pending_review_is_invalid_status(client, auth, insert_request,
                                                         read_row, status):
    request_id = insert_request("alice", status=status, version=2)
    before = read_row(request_id)
    assert_rejected(approve(client, auth, "bob", request_id, 2),
                    422, "invalid_status", read_row, request_id, before)
    assert_rejected(request_changes(client, auth, "bob", request_id, 2),
                    422, "invalid_status", read_row, request_id, before)


# --- Scenario 6: reason required -------------------------------------------------------------


@pytest.mark.parametrize("reason", [None, "", "   ", "r" * 10_001],
                         ids=["missing", "empty", "blank", "too-long"])
def test_request_changes_without_valid_reason_is_invalid_input(client, auth, insert_request,
                                                              read_row, reason):
    request_id = insert_request("alice", status="PendingReview", version=2)
    before = read_row(request_id)
    assert_rejected(request_changes(client, auth, "bob", request_id, 2, reason=reason),
                    400, "invalid_input", read_row, request_id, before)


def test_approve_without_version_is_invalid_input(client, auth, insert_request, read_row):
    request_id = insert_request("alice", status="PendingReview", version=2)
    before = read_row(request_id)
    response = client.post(f"/change-requests/{request_id}/approve", json={},
                           headers=auth("bob"))
    assert_rejected(response, 400, "invalid_input", read_row, request_id, before)


# --- Reviewer visibility (FR-015) ---------------------------------------------------------------


def test_reviewer_views_any_request(client, auth, insert_request):
    request_id = insert_request("alice")
    response = client.get(f"/change-requests/{request_id}", headers=auth("bob"))
    assert response.status_code == 200
    assert response.json()["requester_id"] == "alice"


# --- Role removed mid-flow (FR-023) ---------------------------------------------------------------


def test_reviewer_who_lost_the_role_is_rejected_and_others_can_still_review(
    client, auth, insert_request, read_row, remove_role
):
    request_id = insert_request("alice", status="PendingReview", version=2)
    before = read_row(request_id)
    remove_role("bob", "reviewer")
    # Without the Reviewer role bob can no longer see alice's request, so FR-015 and the
    # FR-020 order report "not found" (step 2) before any permission check.
    assert_rejected(approve(client, auth, "bob", request_id, 2),
                    404, "not_found", read_row, request_id, before)
    response = approve(client, auth, "erin", request_id, 2)
    assert response.status_code == 200
    assert read_row(request_id)["status"] == "Approved"
