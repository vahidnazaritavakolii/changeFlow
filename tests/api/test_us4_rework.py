"""US4 over HTTP (T040): correct a returned request, resubmit, approve. Rows checked."""

TEXT = {"title": "Corrected", "description": "With rollback plan", "reason": "Audit"}


def assert_error(response, status, code):
    assert response.status_code == status, response.text
    assert response.json()["error"]["code"] == code


def returned(insert_request, requester="alice"):
    return insert_request(requester, status="ChangesRequested", version=3,
                          changes_requested_reason="Add a rollback plan")


# --- Scenario 1: edit a returned request --------------------------------------------


def test_owner_edits_returned_request(client, auth, insert_request, read_row):
    request_id = returned(insert_request)
    response = client.put(f"/change-requests/{request_id}", json={**TEXT, "version": 3},
                          headers=auth("alice"))
    assert response.status_code == 200
    row = read_row(request_id)
    assert (row["status"], row["version"], row["title"], row["changes_requested_reason"]) == (
        "ChangesRequested",
        4,
        "Corrected",
        "Add a rollback plan",
    )


def test_requester_sees_reviewer_reason(client, auth, insert_request):
    request_id = returned(insert_request)
    body = client.get(f"/change-requests/{request_id}", headers=auth("alice")).json()
    assert (body["status"], body["changes_requested_reason"]) == (
        "ChangesRequested",
        "Add a rollback plan",
    )


# --- Scenario 2: resubmit ---------------------------------------------------------------


def test_owner_resubmits_returned_request(client, auth, insert_request, read_row):
    request_id = returned(insert_request)
    response = client.post(f"/change-requests/{request_id}/submit", json={"version": 3},
                           headers=auth("alice"))
    assert response.status_code == 200
    row = read_row(request_id)
    assert (row["status"], row["version"], row["changes_requested_reason"]) == (
        "PendingReview",
        4,
        "Add a rollback plan",
    )


# --- Scenario 3: others cannot correct or resubmit ---------------------------------------


def test_other_users_cannot_edit_or_resubmit(client, auth, insert_request, read_row):
    hidden_id = returned(insert_request, requester="carol")
    visible_id = returned(insert_request, requester="alice")
    hidden_before, visible_before = read_row(hidden_id), read_row(visible_id)

    for response in (
        client.put(f"/change-requests/{hidden_id}", json={**TEXT, "version": 3},
                   headers=auth("alice")),
        client.post(f"/change-requests/{hidden_id}/submit", json={"version": 3},
                    headers=auth("alice")),
    ):
        assert_error(response, 404, "not_found")
    for response in (
        client.put(f"/change-requests/{visible_id}", json={**TEXT, "version": 3},
                   headers=auth("bob")),
        client.post(f"/change-requests/{visible_id}/submit", json={"version": 3},
                    headers=auth("bob")),
    ):
        assert_error(response, 403, "forbidden")

    assert read_row(hidden_id) == hidden_before
    assert read_row(visible_id) == visible_before


# --- Scenario 4: approve after resubmission; then no more edits --------------------------


def test_resubmitted_request_is_approved_and_then_locked(client, auth, insert_request,
                                                        read_row):
    request_id = returned(insert_request)
    assert client.post(f"/change-requests/{request_id}/submit", json={"version": 3},
                       headers=auth("alice")).status_code == 200
    approve = client.post(f"/change-requests/{request_id}/approve", json={"version": 4},
                          headers=auth("bob"))
    assert approve.status_code == 200
    approved_row = read_row(request_id)
    assert (approved_row["status"], approved_row["version"]) == ("Approved", 5)

    edit = client.put(f"/change-requests/{request_id}", json={**TEXT, "version": 5},
                      headers=auth("alice"))
    assert_error(edit, 422, "invalid_status")
    assert read_row(request_id) == approved_row


# --- End to end over HTTP ------------------------------------------------------------------


def test_full_rework_cycle_over_http(client, auth, read_row):
    created = client.post("/change-requests", json={"title": "v1", "description": "D",
                                                    "reason": "R"}, headers=auth("alice"))
    assert created.status_code == 201
    request_id = created.json()["id"]
    base = f"/change-requests/{request_id}"

    steps = [
        ("alice", "post", f"{base}/submit", {"version": 1}, "PendingReview"),
        ("bob", "post", f"{base}/request-changes", {"version": 2, "reason": "Add tests"},
         "ChangesRequested"),
        ("alice", "put", base, {"title": "v2", "description": "D + tests", "reason": "R",
                                "version": 3}, "ChangesRequested"),
        ("alice", "post", f"{base}/submit", {"version": 4}, "PendingReview"),
        ("bob", "post", f"{base}/approve", {"version": 5}, "Approved"),
    ]
    for expected_version, (user, method, path, body, status) in enumerate(steps, start=2):
        response = getattr(client, method)(path, json=body, headers=auth(user))
        assert response.status_code == 200, response.text
        row = read_row(request_id)
        assert (row["status"], row["version"]) == (status, expected_version)

    final = read_row(request_id)
    assert (final["title"], final["description"], final["changes_requested_reason"]) == (
        "v2",
        "D + tests",
        "Add tests",
    )


def test_new_request_reaches_approved_in_three_operations(client, auth, read_row):
    """SC-005: create and submit by the requester, approve by a different reviewer."""
    created = client.post("/change-requests", json={"title": "T", "description": "D",
                                                    "reason": "R"}, headers=auth("alice"))
    request_id = created.json()["id"]
    submitted = client.post(f"/change-requests/{request_id}/submit", json={"version": 1},
                            headers=auth("alice"))
    approved = client.post(f"/change-requests/{request_id}/approve", json={"version": 2},
                           headers=auth("bob"))
    assert [created.status_code, submitted.status_code, approved.status_code] == [201, 200, 200]
    assert read_row(request_id)["status"] == "Approved"
