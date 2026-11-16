"""Application-level outcome errors."""


class Unauthenticated(Exception):
    def __init__(self, message: str = "Authentication required.") -> None:
        self.message = message
        super().__init__(message)
