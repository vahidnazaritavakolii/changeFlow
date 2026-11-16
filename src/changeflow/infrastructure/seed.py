"""Development-only user provisioning (research R3).

Usage:
    python -m changeflow.infrastructure.seed --db changeflow.db alice=requester bob=reviewer

Prints one ``export <USER>_TOKEN=<token>`` line per user. Only the token hash is stored.
"""

import argparse
import secrets
from collections.abc import Iterable

from changeflow.infrastructure.sqlite_db import connect, hash_token, init_schema


def create_user(db_path: str, user_id: str, roles: Iterable[str]) -> str:
    init_schema(db_path)
    token = secrets.token_urlsafe(32)
    conn = connect(db_path)
    try:
        with conn:
            conn.execute(
                "INSERT INTO users (id, token_hash) VALUES (?, ?)",
                (user_id, hash_token(token)),
            )
            conn.executemany(
                "INSERT INTO user_roles (user_id, role) VALUES (?, ?)",
                [(user_id, role) for role in roles],
            )
    finally:
        conn.close()
    return token


def parse_user_spec(spec: str) -> tuple[str, list[str]]:
    user_id, _, roles = spec.partition("=")
    if not user_id:
        raise argparse.ArgumentTypeError(f"invalid user spec: {spec!r}")
    return user_id, [role for role in roles.split(",") if role]


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Create ChangeFlow users (development only).")
    parser.add_argument("--db", default="changeflow.db", help="SQLite database file")
    parser.add_argument(
        "users",
        nargs="+",
        type=parse_user_spec,
        metavar="user=role[,role]",
        help="roles: requester, reviewer (may be empty: 'dave=')",
    )
    args = parser.parse_args(argv)
    for user_id, roles in args.users:
        token = create_user(args.db, user_id, roles)
        print(f"export {user_id.upper()}_TOKEN={token}")


if __name__ == "__main__":
    main()
