"""SQLite connection, schema and token hashing (research R1, R3)."""

import hashlib
import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id          TEXT PRIMARY KEY,
    token_hash  TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS user_roles (
    user_id  TEXT NOT NULL REFERENCES users(id),
    role     TEXT NOT NULL CHECK (role IN ('requester', 'reviewer')),
    PRIMARY KEY (user_id, role)
);

CREATE TABLE IF NOT EXISTS change_requests (
    id                        INTEGER PRIMARY KEY AUTOINCREMENT,
    title                     TEXT NOT NULL,
    description               TEXT NOT NULL,
    reason                    TEXT NOT NULL,
    requester_id              TEXT NOT NULL REFERENCES users(id),
    status                    TEXT NOT NULL CHECK (status IN
                                ('Draft', 'PendingReview', 'ChangesRequested', 'Approved')),
    version                   INTEGER NOT NULL CHECK (version >= 1),
    changes_requested_reason  TEXT NULL
);
"""


def connect(db_path: str) -> sqlite3.Connection:
    """Open a connection; concurrent writers wait up to 5 s for the lock."""
    conn = sqlite3.connect(db_path, timeout=5.0)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def init_schema(db_path: str) -> None:
    """Create the tables if they do not exist (idempotent)."""
    conn = connect(db_path)
    try:
        conn.executescript(SCHEMA)
    finally:
        conn.close()


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
