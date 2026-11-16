"""HTTP handlers: parse the request, call exactly one use case, return the result.

Handlers contain no conditions (enforced by tests/architecture/test_architecture.py).
"""

from fastapi import APIRouter, Request

from changeflow.application.use_cases import UseCases

router = APIRouter()


def get_use_cases(request: Request) -> UseCases:
    return request.app.state.use_cases
