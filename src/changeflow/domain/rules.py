"""Domain rules: visibility, validation, version and status checks (FR-020).

Standard library only (Constitution Principle I).
"""

from changeflow.domain.errors import Conflict, InvalidInput, InvalidStatus
from changeflow.domain.model import TRANSITIONS, Actor, ChangeRequest, Role, Status

# Field limits (spec assumption A6, still open): defined once here so a decision
# on A6 is a single edit.
TITLE_MAX = 200
TEXT_MAX = 10_000
FIELD_LIMITS = {"title": TITLE_MAX, "description": TEXT_MAX, "reason": TEXT_MAX}


def is_visible(actor: Actor, request: ChangeRequest) -> bool:
    """FR-015: reviewers see all; the requester always sees their own request."""
    return Role.REVIEWER in actor.roles or request.requester_id == actor.user_id


def validate_body(body: object) -> dict:
    if not isinstance(body, dict):
        raise InvalidInput("The request body must be a JSON object.")
    return body


def validate_text(body: dict, *field_names: str) -> dict[str, str]:
    """FR-004/PA-5: present, a string, non-blank after trimming, within A6 limits.

    Values are returned as given (not trimmed).
    """
    values: dict[str, str] = {}
    for name in field_names:
        value = body.get(name)
        if not isinstance(value, str):
            raise InvalidInput(f"'{name}' is required and must be a string.")
        if not value.strip():
            raise InvalidInput(f"'{name}' must not be blank.")
        limit = FIELD_LIMITS[name]
        if len(value) > limit:
            raise InvalidInput(f"'{name}' must be at most {limit} characters.")
        values[name] = value
    return values


def validate_version(body: dict) -> int:
    """'version' must be a JSON integer >= 1 (booleans and strings are invalid)."""
    version = body.get("version")
    if type(version) is not int or version < 1:
        raise InvalidInput("'version' is required and must be an integer >= 1.")
    return version


def check_version(request: ChangeRequest, version: int) -> None:
    if request.version != version:
        raise Conflict()


def next_status(request: ChangeRequest, operation: str) -> Status:
    target = TRANSITIONS.get((request.status, operation))
    if target is None:
        raise InvalidStatus(
            f"'{operation}' is not allowed when the request is {request.status.value}."
        )
    return target
