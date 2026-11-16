"""Domain rules: visibility, validation, version and status checks (FR-020).

Standard library only (Constitution Principle I).
"""

from dataclasses import replace

from changeflow.domain.errors import Conflict, Forbidden, InvalidInput, InvalidStatus
from changeflow.domain.model import (
    EDIT,
    SUBMIT,
    TRANSITIONS,
    Actor,
    ChangeRequest,
    Role,
    Status,
)

# Field limits (spec assumption A6, still open): defined once here so a decision
# on A6 is a single edit.
TITLE_MAX = 200
TEXT_MAX = 10_000
FIELD_LIMITS = {"title": TITLE_MAX, "description": TEXT_MAX, "reason": TEXT_MAX}


def sees_all_requests(actor: Actor) -> bool:
    """FR-015(b): a user currently holding the Reviewer role sees every request."""
    return Role.REVIEWER in actor.roles


def is_visible(actor: Actor, request: ChangeRequest) -> bool:
    """FR-015: reviewers see all; the requester always sees their own request."""
    return sees_all_requests(actor) or request.requester_id == actor.user_id


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


# --- Requester operations (FR-005..FR-009). Each applies FR-020 steps 3 -> 6. ---


def _require_requester_role(actor: Actor) -> None:
    if Role.REQUESTER not in actor.roles:
        raise Forbidden("The Requester role is required.")


def _require_owning_requester(actor: Actor, request: ChangeRequest) -> None:
    if request.requester_id != actor.user_id:
        raise Forbidden("Only the request's requester may do this.")
    _require_requester_role(actor)


def create_request(actor: Actor, body: object) -> ChangeRequest:
    _require_requester_role(actor)  # step 3
    text = validate_text(validate_body(body), "title", "description", "reason")  # step 4
    return ChangeRequest(
        id=None,
        title=text["title"],
        description=text["description"],
        reason=text["reason"],
        requester_id=actor.user_id,
        status=Status.DRAFT,
        version=1,
        changes_requested_reason=None,
    )


def edit(actor: Actor, request: ChangeRequest, body: object) -> ChangeRequest:
    """Replace title, description and reason together (PA-4); keeps the reason (PA-1)."""
    _require_owning_requester(actor, request)  # step 3
    data = validate_body(body)  # step 4
    text = validate_text(data, "title", "description", "reason")
    version = validate_version(data)
    check_version(request, version)  # step 5
    status = next_status(request, EDIT)  # step 6
    return replace(request, status=status, **text)


def submit(actor: Actor, request: ChangeRequest, body: object) -> ChangeRequest:
    _require_owning_requester(actor, request)  # step 3
    version = validate_version(validate_body(body))  # step 4
    check_version(request, version)  # step 5
    return replace(request, status=next_status(request, SUBMIT))  # step 6
