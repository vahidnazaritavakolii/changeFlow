"""Domain model: roles, statuses, actors, change requests and the workflow table.

Standard library only (Constitution Principle I).
"""

from dataclasses import dataclass
from enum import Enum


class Role(str, Enum):
    REQUESTER = "requester"
    REVIEWER = "reviewer"


class Status(str, Enum):
    DRAFT = "Draft"
    PENDING_REVIEW = "PendingReview"
    CHANGES_REQUESTED = "ChangesRequested"
    APPROVED = "Approved"


EDIT = "edit"
SUBMIT = "submit"
APPROVE = "approve"
REQUEST_CHANGES = "request_changes"

# Single source of truth for the workflow (FR-002). Approved is terminal (FR-017);
# there is no delete operation (FR-021).
TRANSITIONS: dict[tuple[Status, str], Status] = {
    (Status.DRAFT, EDIT): Status.DRAFT,
    (Status.CHANGES_REQUESTED, EDIT): Status.CHANGES_REQUESTED,
    (Status.DRAFT, SUBMIT): Status.PENDING_REVIEW,
    (Status.CHANGES_REQUESTED, SUBMIT): Status.PENDING_REVIEW,
    (Status.PENDING_REVIEW, APPROVE): Status.APPROVED,
    (Status.PENDING_REVIEW, REQUEST_CHANGES): Status.CHANGES_REQUESTED,
}


@dataclass(frozen=True)
class Actor:
    """The authenticated caller of one operation, with roles read at its start."""

    user_id: str
    roles: frozenset[Role]


@dataclass(frozen=True)
class ChangeRequest:
    id: int | None
    title: str
    description: str
    reason: str
    requester_id: str
    status: Status
    # Integer >= 1; 1 on create; +1 on every successful modification.
    version: int
    # Holds only the most recent reason; None until the first RequestChanges.
    changes_requested_reason: str | None
