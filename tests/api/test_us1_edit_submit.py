"""US1 over HTTP (T027): edit and submit. Every rejection checks the stored row (SC-003)."""

import pytest

TEXT = {"title": "New title", "description": "New description", "reason": "New reason"}


def assert_error(response, status, code):
    assert response.status_code == status, response.text
    assert response.json()["error"]["code"] == code


def edit(client, auth, user, request_id, **body):
    return client.put(f"/change-requests/{request_id}", json=body, headers=auth(user))


def submit(client, auth, user, request_id, version):
    return client.post(
        f"/change-requests/{request_id}/submit", json={"version": version}, headers=auth(user)
    )


# --- Allowed (scenarios 2, 3) ---------------------------------------------------------


def test_owner_edits_draft(client, auth, insert_request, read_row):
    request_id = insert_request("alice")
    response = edit(client, auth, "alice", request_id, **TEXT, version=1)
    assert response.status_code == 200
    assert response.json()["version"] == 2
    row = read_row(request_id)
    assert (row["title"], row["description"], row["reason"]) == (
        "New title",
        "New description",
        "New reason",
    )
    assert (row["status"], row["version"]) == ("Draft", 2)


def test_owner_submits_draft(client, auth, insert_request, read_row):
    request_id = insert_request("alice")
    response = submit(client, auth, "alice", request_id, 1)
    assert response.status_code == 200
    assert (response.json()["status"], response.json()["version"]) == ("PendingReview", 2)
    row = read_row(request_id)
    assert (row["status"], row["version"]) == ("PendingReview", 2)


def test_edit_with_identical_values_increments_version(client, auth, insert_request, read_row):
    request_id = insert_request("alice", title="T", description="D", reason="R")
    response = edit(client, auth, "alice", request_id, title="T", description="D", reason="R",
                    version=1)
    assert response.status_code == 200
    assert read_row(request_id)["version"] == 2


def test_unknown_extra_field_is_ignored(client, auth, insert_request, read_row):
    request_id = insert_request("alice")
    response = edit(client, auth, "alice", request_id, **TEXT, version=1, status="Approved",
                    priority="high")
    assert response.status_code == 200
    assert "priority" not in response.json()
    row = read_row(request_id)
    assert (row["status"], row["version"]) == ("Draft", 2)


# --- Rejected -------------------------------------------------------------------------------


def assert_rejected(response, status, code, read_row, request_id, before):
    assert_error(response, status, code)
    assert read_row(request_id) == before


def test_other_requesters_cannot_see_or_change_draft(client, auth, insert_request, read_row):
    request_id = insert_request("carol")
    before = read_row(request_id)
    assert_rejected(edit(client, auth, "alice", request_id, **TEXT, version=1),
                    404, "not_found", read_row, request_id, before)
    assert_rejected(submit(client, auth, "alice", request_id, 1),
                    404, "not_found", read_row, request_id, before)


def test_reviewer_cannot_edit_or_submit_someone_elses_draft(client, auth, insert_request,
                                                             read_row):
    request_id = insert_request("alice")
    before = read_row(request_id)
    assert_rejected(edit(client, auth, "bob", request_id, **TEXT, version=1),
                    403, "forbidden", read_row, request_id, before)
    assert_rejected(submit(client, auth, "bob", request_id, 1),
                    403, "forbidden", read_row, request_id, before)


def test_owner_who_lost_requester_role_can_view_but_not_change(client, auth, insert_request,
                                                                read_row, remove_role):
    request_id = insert_request("alice")
    before = read_row(request_id)
    remove_role("alice", "requester")
    assert client.get(f"/change-requests/{request_id}", headers=auth("alice")).status_code == 200
    assert_rejected(edit(client, auth, "alice", request_id, **TEXT, version=1),
                    403, "forbidden", read_row, request_id, before)
    assert_rejected(submit(client, auth, "alice", request_id, 1),
                    403, "forbidden", read_row, request_id, before)


@pytest.mark.parametrize("status", ["PendingReview", "Approved"])
def test_edit_outside_draft_is_invalid_status(client, auth, insert_request, read_row, status):
    request_id = insert_request("alice", status=status, version=3)
    before = read_row(request_id)
    assert_rejected(edit(client, auth, "alice", request_id, **TEXT, version=3),
                    422, "invalid_status", read_row, request_id, before)


def test_missing_version_is_invalid_input(client, auth, insert_request, read_row):
    request_id = insert_request("alice")
    before = read_row(request_id)
    assert_rejected(edit(client, auth, "alice", request_id, **TEXT),
                    400, "invalid_input", read_row, request_id, before)
    assert_rejected(
        client.post(f"/change-requests/{request_id}/submit", json={}, headers=auth("alice")),
        400, "invalid_input", read_row, request_id, before)


@pytest.mark.parametrize("content", [b"not json", b"", b"[1, 2]"])
def test_non_object_body_is_invalid_input(client, auth, insert_request, read_row, content):
    request_id = insert_request("alice")
    before = read_row(request_id)
    response = client.put(f"/change-requests/{request_id}", content=content,
                          headers=auth("alice"))
    assert_rejected(response, 400, "invalid_input", read_row, request_id, before)


def test_stale_version_is_conflict(client, auth, insert_request, read_row):
    request_id = insert_request("alice", version=2)
    before = read_row(request_id)
    assert_rejected(edit(client, auth, "alice", request_id, **TEXT, version=1),
                    409, "conflict", read_row, request_id, before)


def test_repeated_submit(client, auth, insert_request, read_row):
    request_id = insert_request("alice")
    assert submit(client, auth, "alice", request_id, 1).status_code == 200
    before = read_row(request_id)
    assert_rejected(submit(client, auth, "alice", request_id, 1),
                    409, "conflict", read_row, request_id, before)
    assert_rejected(submit(client, auth, "alice", request_id, 2),
                    422, "invalid_status", read_row, request_id, before)


def test_invalid_input_reported_before_conflict(client, auth, insert_request, read_row):
    request_id = insert_request("alice", version=4)
    before = read_row(request_id)
    assert_rejected(edit(client, auth, "alice", request_id, **{**TEXT, "title": " "}, version=1),
                    400, "invalid_input", read_row, request_id, before)
