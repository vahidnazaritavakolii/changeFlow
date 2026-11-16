"""SQLite implementation of ChangeRequestRepository (research R1, R2)."""

import sqlite3
from dataclasses import replace

from changeflow.domain.model import ChangeRequest, Status
from changeflow.infrastructure.sqlite_db import connect

_COLUMNS = (
    "id, title, description, reason, requester_id, status, version, changes_requested_reason"
)


def _to_entity(row: sqlite3.Row) -> ChangeRequest:
    return ChangeRequest(
        id=row["id"],
        title=row["title"],
        description=row["description"],
        reason=row["reason"],
        requester_id=row["requester_id"],
        status=Status(row["status"]),
        version=row["version"],
        changes_requested_reason=row["changes_requested_reason"],
    )


class SqliteChangeRequestRepository:
    def __init__(self, db_path: str) -> None:
        self._db_path = db_path

    def get(self, id: int) -> ChangeRequest | None:
        conn = connect(self._db_path)
        try:
            row = conn.execute(
                f"SELECT {_COLUMNS} FROM change_requests WHERE id = ?", (id,)
            ).fetchone()
        finally:
            conn.close()
        return _to_entity(row) if row is not None else None

    def add(self, request: ChangeRequest) -> ChangeRequest:
        conn = connect(self._db_path)
        try:
            with conn:
                cursor = conn.execute(
                    "INSERT INTO change_requests (title, description, reason, requester_id,"
                    " status, version, changes_requested_reason)"
                    " VALUES (?, ?, ?, ?, ?, 1, ?)",
                    (
                        request.title,
                        request.description,
                        request.reason,
                        request.requester_id,
                        request.status.value,
                        request.changes_requested_reason,
                    ),
                )
        finally:
            conn.close()
        return replace(request, id=cursor.lastrowid, version=1)

    def update_if_version(self, request: ChangeRequest, expected_version: int) -> bool:
        # A single conditional statement: atomic check-and-write (research R2).
        conn = connect(self._db_path)
        try:
            with conn:
                cursor = conn.execute(
                    "UPDATE change_requests SET title = ?, description = ?, reason = ?,"
                    " status = ?, changes_requested_reason = ?, version = version + 1"
                    " WHERE id = ? AND version = ?",
                    (
                        request.title,
                        request.description,
                        request.reason,
                        request.status.value,
                        request.changes_requested_reason,
                        request.id,
                        expected_version,
                    ),
                )
        finally:
            conn.close()
        return cursor.rowcount == 1

    def list_all(self) -> list[ChangeRequest]:
        return self._list(f"SELECT {_COLUMNS} FROM change_requests ORDER BY id", ())

    def list_by_requester(self, user_id: str) -> list[ChangeRequest]:
        return self._list(
            f"SELECT {_COLUMNS} FROM change_requests WHERE requester_id = ? ORDER BY id",
            (user_id,),
        )

    def _list(self, sql: str, params: tuple) -> list[ChangeRequest]:
        conn = connect(self._db_path)
        try:
            rows = conn.execute(sql, params).fetchall()
        finally:
            conn.close()
        return [_to_entity(row) for row in rows]
