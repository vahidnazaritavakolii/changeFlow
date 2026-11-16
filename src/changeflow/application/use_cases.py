"""Use cases: authenticate -> load visible -> Domain -> save (FR-020).

Depends only on the Domain and on the ports in this package (Constitution Principle I).
"""

from dataclasses import replace

from changeflow.application.errors import Unauthenticated
from changeflow.application.ports import ChangeRequestRepository, UserDirectory
from changeflow.domain import rules
from changeflow.domain.errors import Conflict, NotFound
from changeflow.domain.model import Actor, ChangeRequest


class UseCases:
    def __init__(self, repository: ChangeRequestRepository, users: UserDirectory) -> None:
        self._repository = repository
        self._users = users

    # FR-020 step 1: identity.
    def _authenticate(self, token: str | None) -> Actor:
        if not token:
            raise Unauthenticated()
        actor = self._users.find_actor_by_token(token)
        if actor is None:
            raise Unauthenticated()
        return actor

    # FR-020 step 2: existence and visibility (PA-6: non-numeric id is not found).
    def _load_visible(self, actor: Actor, raw_id: str) -> ChangeRequest:
        if not (raw_id.isascii() and raw_id.isdigit()):
            raise NotFound()
        request = self._repository.get(int(raw_id))
        if request is None or not rules.is_visible(actor, request):
            raise NotFound()
        return request

    # FR-020 step 7: conditional write on the loaded version (research R2).
    def _save(self, updated: ChangeRequest, loaded_version: int) -> ChangeRequest:
        if not self._repository.update_if_version(updated, loaded_version):
            raise Conflict()
        return replace(updated, version=loaded_version + 1)

    # --- User Story 1 ----------------------------------------------------------

    def create(self, token: str | None, body: object) -> ChangeRequest:
        actor = self._authenticate(token)
        return self._repository.add(rules.create_request(actor, body))

    def get(self, token: str | None, raw_id: str) -> ChangeRequest:
        actor = self._authenticate(token)
        return self._load_visible(actor, raw_id)

    def list_requests(self, token: str | None) -> list[ChangeRequest]:
        """FR-015, PA-2, PA-3: reviewers get all; everyone else gets their own."""
        actor = self._authenticate(token)
        if rules.sees_all_requests(actor):
            return self._repository.list_all()
        return self._repository.list_by_requester(actor.user_id)

    def edit(self, token: str | None, raw_id: str, body: object) -> ChangeRequest:
        actor = self._authenticate(token)
        loaded = self._load_visible(actor, raw_id)
        return self._save(rules.edit(actor, loaded, body), loaded.version)

    def submit(self, token: str | None, raw_id: str, body: object) -> ChangeRequest:
        actor = self._authenticate(token)
        loaded = self._load_visible(actor, raw_id)
        return self._save(rules.submit(actor, loaded, body), loaded.version)
