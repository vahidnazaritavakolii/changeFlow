"""Outcome -> HTTP mapping (contracts/http-api.md, research R6)."""

from fastapi import Request
from fastapi.responses import JSONResponse

from changeflow.application.errors import Unauthenticated
from changeflow.domain.errors import Conflict, Forbidden, InvalidInput, InvalidStatus, NotFound

ERROR_MAP: dict[type[Exception], tuple[int, str]] = {
    Unauthenticated: (401, "unauthenticated"),
    NotFound: (404, "not_found"),
    Forbidden: (403, "forbidden"),
    InvalidInput: (400, "invalid_input"),
    Conflict: (409, "conflict"),
    InvalidStatus: (422, "invalid_status"),
}

_EXTRA_HEADERS: dict[int, dict[str, str]] = {401: {"WWW-Authenticate": "Bearer"}}


async def outcome_error_handler(request: Request, exc: Exception) -> JSONResponse:
    status, code = ERROR_MAP[type(exc)]
    return JSONResponse(
        status_code=status,
        content={"error": {"code": code, "message": getattr(exc, "message", str(exc))}},
        headers=_EXTRA_HEADERS.get(status),
    )
