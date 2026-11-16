"""US1 over HTTP (T026): create, view, list, authentication, visibility.

Every rejection also checks the stored state (SC-003).
"""

import pytest

TEXT = {"title": "Add export", "description": "CSV export", "reason": "Audit"}


def assert_error(response, status, code):
    assert response.status_code == status, response.text
    assert response.json()["error"]["code"] == code


# --- Create (scenarios 1, 4, 5) ---------------------------------------------------


def test_requester_creates_draft(client, auth, read_row):
    response = client.post("/change-requests", json=TEXT, headers=auth("alice"))
    assert response.status_code == 201
    body = response.json()
    assert body == {
        "id": body["id"],
        "title": "Add export",
        "description": "CSV export",
        "reason": "Audit",
        "requester_id": "alice",
        "status": "Draft",
        "version": 1,
        "changes_requested_reason": None,
    }
    row = read_row(body["id"])
    assert (row["status"], row["version"], row["requester_id"]) == ("Draft", 1, "alice")
    assert (row["title"], row["description"], row["reason"]) == (
        "Add export",
        "CSV export",
        "Audit",
    )


@pytest.mark.parametrize("user", ["bob", "dave"])
def test_create_without_requester_role_is_forbidden(client, auth, read_row, user):
    response = client.post("/change-requests", json=TEXT, headers=auth(user))
    assert_error(response, 403, "forbidden")
    assert read_row(1) is None


def test_create_forbidden_before_invalid_input(client, auth, read_row):
    response = client.post("/change-requests", json={"title": ""}, headers=auth("bob"))
    assert_error(response, 403, "forbidden")
    assert read_row(1) is None


@pytest.mark.parametrize(
    "body",
    [
        {"description": "D", "reason": "R"},
        {**TEXT, "title": "   "},
        {**TEXT, "title": "t" * 201},
        {**TEXT, "reason": "r" * 10_001},
    ],
    ids=["missing", "blank", "title-too-long", "reason-too-long"],
)
def test_create_with_invalid_fields_is_invalid_input(client, auth, read_row, body):
    response = client.post("/change-requests", json=body, headers=auth("alice"))
    assert_error(response, 400, "invalid_input")
    assert read_row(1) is None


def test_create_with_non_json_body_is_invalid_input(client, auth, read_row):
    response = client.post("/change-requests", content=b"not json", headers=auth("alice"))
    assert_error(response, 400, "invalid_input")
    assert read_row(1) is None


# --- Authentication (scenario 7) ------------------------------------------------------

BAD_HEADERS = [
    {},
    {"Authorization": "Token abc"},
    {"Authorization": "Bearer"},
    {"Authorization": "Bearer unknown-token"},
]


@pytest.mark.parametrize("headers", BAD_HEADERS, ids=["none", "scheme", "empty", "unknown"])
def test_unauthenticated_calls_are_rejected(client, insert_request, read_row, headers):
    request_id = insert_request("alice")
    before = read_row(request_id)
    for response in (
        client.post("/change-requests", json=TEXT, headers=headers),
        client.get("/change-requests", headers=headers),
        client.get(f"/change-requests/{request_id}", headers=headers),
        client.get("/change-requests/999", headers=headers),
    ):
        assert_error(response, 401, "unauthenticated")
        assert response.headers["WWW-Authenticate"] == "Bearer"
    assert read_row(request_id) == before
    assert read_row(request_id + 1) is None


# --- View ---------------------------------------------------------------------------------


def test_owner_views_own_request(client, auth, insert_request):
    request_id = insert_request("alice", changes_requested_reason="why")
    response = client.get(f"/change-requests/{request_id}", headers=auth("alice"))
    assert response.status_code == 200
    assert response.json()["changes_requested_reason"] == "why"


def test_owner_without_any_role_views_own_request(client, auth, insert_request):
    request_id = insert_request("dave")
    response = client.get(f"/change-requests/{request_id}", headers=auth("dave"))
    assert response.status_code == 200
    assert response.json()["requester_id"] == "dave"


@pytest.mark.parametrize("raw_id", ["999", "abc", "1.5", "-1"])
def test_unknown_or_non_numeric_id_is_not_found(client, auth, insert_request, raw_id):
    insert_request("alice")
    response = client.get(f"/change-requests/{raw_id}", headers=auth("alice"))
    assert_error(response, 404, "not_found")


def test_request_of_another_user_is_hidden(client, auth, insert_request):
    request_id = insert_request("carol")
    response = client.get(f"/change-requests/{request_id}", headers=auth("alice"))
    assert_error(response, 404, "not_found")


# --- List (scenario 9) ----------------------------------------------------------------------


def ids_of(response):
    assert response.status_code == 200
    return [item["id"] for item in response.json()["items"]]


def test_listing_respects_visibility(client, auth, insert_request):
    a1 = insert_request("alice")
    c1 = insert_request("carol")
    a2 = insert_request("alice")
    assert ids_of(client.get("/change-requests", headers=auth("alice"))) == [a1, a2]
    assert ids_of(client.get("/change-requests", headers=auth("bob"))) == [a1, c1, a2]
    assert ids_of(client.get("/change-requests", headers=auth("carol"))) == [a1, c1, a2]
    assert client.get("/change-requests", headers=auth("dave")).json() == {"items": []}


def test_owner_without_any_role_lists_own_requests(client, auth, insert_request):
    insert_request("alice")
    d1 = insert_request("dave")
    assert ids_of(client.get("/change-requests", headers=auth("dave"))) == [d1]


# --- Operations that do not exist (FR-019, FR-021) ----------------------------------------


def test_delete_and_unlisted_routes_are_rejected(client, auth, insert_request, read_row):
    request_id = insert_request("alice")
    before = read_row(request_id)
    for response in (
        client.delete(f"/change-requests/{request_id}", headers=auth("alice")),
        client.delete(f"/change-requests/{request_id}", headers=auth("bob")),
        client.post(f"/change-requests/{request_id}/reject", json={"version": 1},
                    headers=auth("bob")),
        client.post(f"/change-requests/{request_id}/cancel", json={"version": 1},
                    headers=auth("alice")),
    ):
        assert response.status_code in (404, 405)
    assert read_row(request_id) == before
