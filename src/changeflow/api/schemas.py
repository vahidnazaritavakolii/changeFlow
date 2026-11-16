"""Response models (output only; request bodies are validated in the Domain, R5)."""

from pydantic import BaseModel

from changeflow.domain.model import ChangeRequest


class ChangeRequestOut(BaseModel):
    id: int
    title: str
    description: str
    reason: str
    requester_id: str
    status: str
    version: int
    changes_requested_reason: str | None


class ChangeRequestList(BaseModel):
    items: list[ChangeRequestOut]


def to_out(request: ChangeRequest) -> ChangeRequestOut:
    return ChangeRequestOut(
        id=request.id,
        title=request.title,
        description=request.description,
        reason=request.reason,
        requester_id=request.requester_id,
        status=request.status.value,
        version=request.version,
        changes_requested_reason=request.changes_requested_reason,
    )
