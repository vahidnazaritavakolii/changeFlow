"""Deterministic concurrency evidence (T036, SC-002, FR-014). Real SQLite, no HTTP.

No timing-dependent stress test: interleavings are constructed explicitly.
"""

from dataclasses import replace

import pytest

from changeflow.application.use_cases import UseCases
from changeflow.domain.errors import Conflict
from changeflow.infrastructure.sqlite_repository import SqliteChangeRequestRepository
from changeflow.infrastructure.sqlite_users import SqliteUserDirectory

TEXT = {"title": "New title", "description": "New description", "reason": "New reason"}


@pytest.fixture
def repo(db_path):
    return SqliteChangeRequestRepository(db_path)


@pytest.fixture
def use_cases(db_path, repo):
    return UseCases(repo, SqliteUserDirectory(db_path))


class StaleReadRepository(SqliteChangeRequestRepository):
    """Returns a snapshot taken earlier from get(), as if this operation had loaded the
    request just before another operation wrote it."""

    def __init__(self, db_path, snapshot):
        super().__init__(db_path)
        self._snapshot = snapshot

    def get(self, id):
        return self._snapshot


def test_write_based_on_an_older_load_writes_nothing(repo, use_cases, tokens, insert_request,
                                                     read_row):
    request_id = insert_request("alice")
    first_copy = repo.get(request_id)
    use_cases.edit(tokens["alice"], str(request_id), {**TEXT, "version": 1})
    after_second_change = read_row(request_id)

    assert repo.update_if_version(replace(first_copy, title="stale"), first_copy.version) is False
    assert read_row(request_id) == after_second_change
    assert after_second_change["version"] == 2


# (operation, user, starting status, body without version)
OPERATIONS = [
    ("edit", "alice", "Draft", TEXT),
    ("submit", "alice", "Draft", {}),
    ("approve", "bob", "PendingReview", {}),
    ("request_changes", "bob", "PendingReview", {"reason": "Fix it"}),
]


@pytest.mark.parametrize("operation,user,status,body", OPERATIONS, ids=[o[0] for o in OPERATIONS])
def test_second_call_with_same_version_is_conflict(use_cases, tokens, insert_request, read_row,
                                                   operation, user, status, body):
    request_id = insert_request("alice", status=status, version=1)
    call = getattr(use_cases, operation)

    call(tokens[user], str(request_id), {**body, "version": 1})
    after_first = read_row(request_id)
    assert after_first["version"] == 2

    with pytest.raises(Conflict):
        call(tokens[user], str(request_id), {**body, "version": 1})
    assert read_row(request_id) == after_first


@pytest.mark.parametrize("operation,user,status,body", OPERATIONS, ids=[o[0] for o in OPERATIONS])
def test_interleaved_operations_on_same_version_exactly_one_succeeds(
    db_path, repo, use_cases, tokens, insert_request, read_row, operation, user, status, body
):
    """Both operations load version 1; the first writes; the second passes every Domain
    check against its stale copy and is stopped by the conditional write (FR-020 step 7)."""
    request_id = insert_request("alice", status=status, version=1)
    stale_snapshot = repo.get(request_id)
    late = UseCases(StaleReadRepository(db_path, stale_snapshot), SqliteUserDirectory(db_path))

    getattr(use_cases, operation)(tokens[user], str(request_id), {**body, "version": 1})
    after_first = read_row(request_id)

    with pytest.raises(Conflict):
        getattr(late, operation)(tokens[user], str(request_id), {**body, "version": 1})
    assert read_row(request_id) == after_first


def test_approve_and_request_changes_race_exactly_one_wins(db_path, repo, use_cases, tokens,
                                                           insert_request, read_row):
    request_id = insert_request("alice", status="PendingReview", version=1)
    stale_snapshot = repo.get(request_id)
    late = UseCases(StaleReadRepository(db_path, stale_snapshot), SqliteUserDirectory(db_path))

    use_cases.approve(tokens["bob"], str(request_id), {"version": 1})
    with pytest.raises(Conflict):
        late.request_changes(tokens["erin"], str(request_id), {"version": 1, "reason": "x"})

    row = read_row(request_id)
    assert (row["status"], row["version"], row["changes_requested_reason"]) == (
        "Approved",
        2,
        None,
    )
