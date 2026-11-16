"""Ports the use cases depend on (research R8). Implemented by infrastructure."""

from typing import Protocol

from changeflow.domain.model import Actor, ChangeRequest


class ChangeRequestRepository(Protocol):
    def get(self, id: int) -> ChangeRequest | None: ...

    def add(self, request: ChangeRequest) -> ChangeRequest:
        """Store a new request; return it with its assigned id and version 1."""
        ...

    def update_if_version(self, request: ChangeRequest, expected_version: int) -> bool:
        """Atomically write the request if its stored version still equals
        expected_version, incrementing the version; return whether it was written."""
        ...

    def list_all(self) -> list[ChangeRequest]: ...

    def list_by_requester(self, user_id: str) -> list[ChangeRequest]: ...


class UserDirectory(Protocol):
    def find_actor_by_token(self, token: str) -> Actor | None:
        """Return the user and their current roles, or None for an unknown token."""
        ...
