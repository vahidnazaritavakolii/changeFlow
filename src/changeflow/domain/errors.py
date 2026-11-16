"""Domain outcome errors. Each maps to one outcome category of the spec (FR-018)."""


class DomainError(Exception):
    default_message = "The operation was rejected."

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.default_message
        super().__init__(self.message)


class NotFound(DomainError):
    default_message = "Change request not found."


class Forbidden(DomainError):
    default_message = "You are not allowed to perform this operation."


class InvalidInput(DomainError):
    default_message = "The request body is invalid."


class Conflict(DomainError):
    default_message = "The change request was modified by someone else; reload it and retry."


class InvalidStatus(DomainError):
    default_message = "The operation is not allowed in the request's current status."
