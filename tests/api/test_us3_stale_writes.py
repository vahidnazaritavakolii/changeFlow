"""US3 over HTTP (T037): stale writes, races and check order. Stored rows are checked."""

import pytest

TEXT = {"title": "New title", "description": "New description", "reason": "New reason"}


def assert_error(response, status, code):
    assert response.status_code == status, response.text
    assert response.json()["error"]["code"] == code


def post(client, auth, user, path, body):
    return client.post(path, json=body, headers=auth(user) if user else {})


# --- Scenario 1: edit based on an outdated version ------------------------------------


def test_edit_based_on_outdated_version_is_conflict(client, auth, insert_request, read_row):
    request_id = insert_request("alice")
    first = client.put(f"/change-requests/{request_id}", json={**TEXT, "version": 1},
                       headers=auth("alice"))
    assert first.status_code == 200
    after_first = read_row(request_id)

    stale = client.put(f"/change-requests/{request_id}",
                       json={"title": "Other", "description": "Other", "reason": "Other",
                             "version": 1},
                       headers=auth("alice"))
    assert_error(stale, 409, "conflict")
    assert read_row(request_id) == after_first
    assert after_first["title"] == "New title"


# --- Scenario 2: two reviewers on the same version ---------------------------------------

DECISIONS = {
    "approve": ("bob", {"version": 2}, "Approved"),
    "request-changes": ("erin", {"version": 2, "reason": "Needs tests"}, "ChangesRequested"),
}


@pytest.mark.parametrize("first,second", [("approve", "request-changes"),
                                          ("request-changes", "approve")])
def test_two_reviewers_on_same_version_exactly_one_wins(client, auth, insert_request, read_row,
                                                        first, second):
    request_id = insert_request("alice", status="PendingReview", version=2)
    responses = {}
    for action in (first, second):
        user, body, _ = DECISIONS[action]
        responses[action] = post(client, auth, user,
                                 f"/change-requests/{request_id}/{action}", body)

    assert responses[first].status_code == 200
    assert_error(responses[second], 409, "conflict")
    row = read_row(request_id)
    assert (row["status"], row["version"]) == (DECISIONS[first][2], 3)


# --- Scenario 3: no rejection changes the stored request ------------------------------------


def test_every_rejection_category_leaves_the_row_unchanged(client, auth, insert_request,
                                                          read_row):
    request_id = insert_request("alice", status="PendingReview", version=2)
    before = read_row(request_id)
    path = f"/change-requests/{request_id}"
    rejections = [
        (client.put(path, json={**TEXT, "version": 2}), 401, "unauthenticated"),
        (post(client, auth, "dave", f"{path}/approve", {"version": 2}), 404, "not_found"),
        (post(client, auth, "alice", f"{path}/approve", {"version": 2}), 403, "forbidden"),
        (post(client, auth, "bob", f"{path}/request-changes", {"version": 2}), 400,
         "invalid_input"),
        (post(client, auth, "bob", f"{path}/approve", {"version": 1}), 409, "conflict"),
        (client.put(path, json={**TEXT, "version": 2}, headers=auth("alice")), 422,
         "invalid_status"),
    ]
    for response, status, code in rejections:
        assert_error(response, status, code)
        assert read_row(request_id) == before


# --- Contract: worked examples of check order (FR-020) ----------------------------------------


def test_no_token_and_unknown_id_is_unauthenticated(client):
    assert_error(client.put("/change-requests/999", json={**TEXT, "version": 1}),
                 401, "unauthenticated")


def test_requester_editing_hidden_request_with_invalid_body_is_not_found(
    client, auth, insert_request, read_row
):
    request_id = insert_request("carol")
    before = read_row(request_id)
    response = client.put(f"/change-requests/{request_id}", content=b"not json",
                          headers=auth("alice"))
    assert_error(response, 404, "not_found")
    assert read_row(request_id) == before


def test_self_approval_with_outdated_version_is_forbidden(client, auth, insert_request,
                                                          read_row):
    request_id = insert_request("carol", status="PendingReview", version=3)
    before = read_row(request_id)
    assert_error(post(client, auth, "carol", f"/change-requests/{request_id}/approve",
                      {"version": 1}), 403, "forbidden")
    assert read_row(request_id) == before


def test_blank_title_with_outdated_version_is_invalid_input(client, auth, insert_request,
                                                            read_row):
    request_id = insert_request("alice", version=3)
    before = read_row(request_id)
    response = client.put(f"/change-requests/{request_id}",
                          json={**TEXT, "title": "  ", "version": 1}, headers=auth("alice"))
    assert_error(response, 400, "invalid_input")
    assert read_row(request_id) == before


def test_resubmit_with_old_version_is_conflict_and_with_current_is_invalid_status(
    client, auth, insert_request, read_row
):
    request_id = insert_request("alice", status="PendingReview", version=2)
    before = read_row(request_id)
    path = f"/change-requests/{request_id}/submit"
    assert_error(post(client, auth, "alice", path, {"version": 1}), 409, "conflict")
    assert_error(post(client, auth, "alice", path, {"version": 2}), 422, "invalid_status")
    assert read_row(request_id) == before
