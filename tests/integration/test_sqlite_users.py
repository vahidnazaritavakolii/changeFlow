"""SQLite user directory tests (T015)."""

import hashlib
import sqlite3

import pytest

from changeflow.domain.model import Actor, Role
from changeflow.infrastructure.sqlite_users import SqliteUserDirectory


@pytest.fixture
def users(db_path):
    return SqliteUserDirectory(db_path)


@pytest.mark.parametrize(
    "user,roles",
    [
        ("alice", {Role.REQUESTER}),
        ("bob", {Role.REVIEWER}),
        ("carol", {Role.REQUESTER, Role.REVIEWER}),
        ("dave", set()),
    ],
)
def test_valid_token_returns_actor_with_current_roles(users, tokens, user, roles):
    assert users.find_actor_by_token(tokens[user]) == Actor(user, frozenset(roles))


def test_unknown_token_returns_none(users, tokens):
    assert users.find_actor_by_token("not-a-real-token") is None


def test_only_the_token_hash_is_stored(db_path, tokens):
    conn = sqlite3.connect(db_path)
    try:
        stored = dict(conn.execute("SELECT id, token_hash FROM users").fetchall())
    finally:
        conn.close()
    for user, token in tokens.items():
        assert token not in stored.values()
        assert stored[user] == hashlib.sha256(token.encode()).hexdigest()


def test_removed_role_is_absent_on_next_lookup(users, tokens, remove_role):
    assert Role.REVIEWER in users.find_actor_by_token(tokens["carol"]).roles
    remove_role("carol", "reviewer")
    assert users.find_actor_by_token(tokens["carol"]) == Actor(
        "carol", frozenset({Role.REQUESTER})
    )
