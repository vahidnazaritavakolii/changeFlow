"""SQLite repository tests against a real temp database file (T014)."""

import sqlite3
from dataclasses import replace

import pytest

from changeflow.domain.model import ChangeRequest, Status
from changeflow.infrastructure.sqlite_repository import SqliteChangeRequestRepository


@pytest.fixture
def repo(db_path, tokens):
    return SqliteChangeRequestRepository(db_path)


def new_request(requester_id="alice", title="T"):
    return ChangeRequest(
        id=None,
        title=title,
        description="D",
        reason="R",
        requester_id=requester_id,
        status=Status.DRAFT,
        version=1,
        changes_requested_reason=None,
    )


def test_add_assigns_increasing_ids_and_version_one(repo, read_row):
    first = repo.add(new_request(title="first"))
    second = repo.add(new_request(title="second"))
    assert first.id is not None and second.id > first.id
    assert first.version == 1 and second.version == 1
    row = read_row(first.id)
    assert row["title"] == "first"
    assert row["status"] == "Draft"
    assert row["version"] == 1
    assert row["requester_id"] == "alice"
    assert row["changes_requested_reason"] is None


def test_get_unknown_id_returns_none(repo):
    assert repo.get(999) is None


def test_get_returns_stored_request(repo, insert_request):
    request_id = insert_request("alice", status="PendingReview", version=4,
                                changes_requested_reason="why")
    request = repo.get(request_id)
    assert request == ChangeRequest(
        id=request_id,
        title="T",
        description="D",
        reason="R",
        requester_id="alice",
        status=Status.PENDING_REVIEW,
        version=4,
        changes_requested_reason="why",
    )


def test_lists_are_ordered_by_id(repo, insert_request):
    a1 = insert_request("alice")
    c1 = insert_request("carol")
    a2 = insert_request("alice")
    assert [r.id for r in repo.list_all()] == [a1, c1, a2]
    assert [r.id for r in repo.list_by_requester("alice")] == [a1, a2]
    assert repo.list_by_requester("dave") == []


def test_update_with_current_version_writes_and_increments(repo, insert_request, read_row):
    request_id = insert_request("alice", version=3)
    loaded = repo.get(request_id)
    updated = replace(
        loaded,
        title="T2",
        description="D2",
        reason="R2",
        status=Status.CHANGES_REQUESTED,
        changes_requested_reason="fix it",
    )
    assert repo.update_if_version(updated, 3) is True
    row = read_row(request_id)
    assert row == {
        "id": request_id,
        "title": "T2",
        "description": "D2",
        "reason": "R2",
        "requester_id": "alice",
        "status": "ChangesRequested",
        "version": 4,
        "changes_requested_reason": "fix it",
    }


@pytest.mark.parametrize("stale_version", [1, 2, 4])
def test_update_with_other_version_writes_nothing(repo, insert_request, read_row, stale_version):
    request_id = insert_request("alice", version=3)
    before = read_row(request_id)
    updated = replace(repo.get(request_id), title="changed")
    assert repo.update_if_version(updated, stale_version) is False
    assert read_row(request_id) == before


def test_status_outside_workflow_cannot_be_inserted(db_path, tokens):
    conn = sqlite3.connect(db_path)
    try:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO change_requests (title, description, reason, requester_id,"
                " status, version) VALUES ('T', 'D', 'R', 'alice', 'Rejected', 1)"
            )
    finally:
        conn.close()


def test_status_outside_workflow_cannot_be_written_by_update(db_path, insert_request, read_row):
    request_id = insert_request("alice")
    conn = sqlite3.connect(db_path)
    try:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "UPDATE change_requests SET status = 'Rejected' WHERE id = ?", (request_id,)
            )
    finally:
        conn.close()
    assert read_row(request_id)["status"] == "Draft"
