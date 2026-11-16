"""SQLite implementation of UserDirectory (research R3).

Roles are read on every call, never cached, so permission checks use current roles.
"""

from changeflow.domain.model import Actor, Role
from changeflow.infrastructure.sqlite_db import connect, hash_token


class SqliteUserDirectory:
    def __init__(self, db_path: str) -> None:
        self._db_path = db_path

    def find_actor_by_token(self, token: str) -> Actor | None:
        conn = connect(self._db_path)
        try:
            user = conn.execute(
                "SELECT id FROM users WHERE token_hash = ?", (hash_token(token),)
            ).fetchone()
            if user is None:
                return None
            roles = conn.execute(
                "SELECT role FROM user_roles WHERE user_id = ?", (user["id"],)
            ).fetchall()
        finally:
            conn.close()
        return Actor(user_id=user["id"], roles=frozenset(Role(r["role"]) for r in roles))
