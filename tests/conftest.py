"""Shared test fixtures (T013).

Each test gets a fresh SQLite file. Stored state is read with a direct sqlite3
connection, independent of the code under test (Constitution Principle IV).
"""

import sqlite3

import pytest

from changeflow.infrastructure.seed import create_user
from changeflow.infrastructure.sqlite_db import init_schema

USERS = {
    "alice": ["requester"],
    "bob": ["reviewer"],
    "erin": ["reviewer"],
    "carol": ["requester", "reviewer"],
    "dave": [],
}


def _connect(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


@pytest.fixture
def db_path(tmp_path):
    path = str(tmp_path / "test.db")
    init_schema(path)
    return path


@pytest.fixture
def tokens(db_path):
    return {user: create_user(db_path, user, roles) for user, roles in USERS.items()}


@pytest.fixture
def auth(tokens):
    def _auth(user):
        return {"Authorization": f"Bearer {tokens[user]}"}

    return _auth


@pytest.fixture
def client(db_path, tokens):
    from fastapi.testclient import TestClient

    from changeflow.api.app import create_app

    with TestClient(create_app(db_path)) as test_client:
        yield test_client


@pytest.fixture
def read_row(db_path):
    def _read_row(request_id):
        conn = _connect(db_path)
        try:
            row = conn.execute(
                "SELECT * FROM change_requests WHERE id = ?", (request_id,)
            ).fetchone()
        finally:
            conn.close()
        return dict(row) if row is not None else None

    return _read_row


@pytest.fixture
def insert_request(db_path, tokens):
    def _insert_request(
        requester_id,
        status="Draft",
        version=1,
        title="T",
        description="D",
        reason="R",
        changes_requested_reason=None,
    ):
        conn = _connect(db_path)
        try:
            with conn:
                cursor = conn.execute(
                    "INSERT INTO change_requests (title, description, reason, requester_id,"
                    " status, version, changes_requested_reason)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (title, description, reason, requester_id, status, version,
                     changes_requested_reason),
                )
        finally:
            conn.close()
        return cursor.lastrowid

    return _insert_request


@pytest.fixture
def remove_role(db_path):
    def _remove_role(user_id, role):
        conn = _connect(db_path)
        try:
            with conn:
                conn.execute(
                    "DELETE FROM user_roles WHERE user_id = ? AND role = ?", (user_id, role)
                )
        finally:
            conn.close()

    return _remove_role
