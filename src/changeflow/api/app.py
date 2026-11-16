"""Composition root: wires SQLite adapters into the use cases (plan.md)."""

import os

from fastapi import FastAPI

from changeflow.api.errors import ERROR_MAP, outcome_error_handler
from changeflow.api.routes import router
from changeflow.application.use_cases import UseCases
from changeflow.infrastructure.sqlite_db import init_schema
from changeflow.infrastructure.sqlite_repository import SqliteChangeRequestRepository
from changeflow.infrastructure.sqlite_users import SqliteUserDirectory


def create_app(db_path: str | None = None) -> FastAPI:
    path = db_path or os.environ.get("CHANGEFLOW_DB", "changeflow.db")
    init_schema(path)
    app = FastAPI(title="ChangeFlow")
    app.state.use_cases = UseCases(
        SqliteChangeRequestRepository(path), SqliteUserDirectory(path)
    )
    app.include_router(router)
    for exc_class in ERROR_MAP:
        app.add_exception_handler(exc_class, outcome_error_handler)
    return app
