"""HTTP handlers: parse the request, call exactly one use case, return the result.

Handlers contain no conditions (enforced by tests/architecture/test_architecture.py).
"""

from fastapi import APIRouter, Depends, Request

from changeflow.api.http_io import bearer_token, json_body
from changeflow.api.schemas import ChangeRequestList, ChangeRequestOut, to_list, to_out
from changeflow.application.use_cases import UseCases

router = APIRouter()


def get_use_cases(request: Request) -> UseCases:
    return request.app.state.use_cases


@router.post("/change-requests", status_code=201, response_model=ChangeRequestOut)
async def create_change_request(
    request: Request, use_cases: UseCases = Depends(get_use_cases)
) -> ChangeRequestOut:
    return to_out(use_cases.create(bearer_token(request), await json_body(request)))


@router.get("/change-requests", response_model=ChangeRequestList)
async def list_change_requests(
    request: Request, use_cases: UseCases = Depends(get_use_cases)
) -> ChangeRequestList:
    return to_list(use_cases.list_requests(bearer_token(request)))


@router.get("/change-requests/{id}", response_model=ChangeRequestOut)
async def get_change_request(
    id: str, request: Request, use_cases: UseCases = Depends(get_use_cases)
) -> ChangeRequestOut:
    return to_out(use_cases.get(bearer_token(request), id))


@router.put("/change-requests/{id}", response_model=ChangeRequestOut)
async def edit_change_request(
    id: str, request: Request, use_cases: UseCases = Depends(get_use_cases)
) -> ChangeRequestOut:
    return to_out(use_cases.edit(bearer_token(request), id, await json_body(request)))


@router.post("/change-requests/{id}/submit", response_model=ChangeRequestOut)
async def submit_change_request(
    id: str, request: Request, use_cases: UseCases = Depends(get_use_cases)
) -> ChangeRequestOut:
    return to_out(use_cases.submit(bearer_token(request), id, await json_body(request)))


@router.post("/change-requests/{id}/approve", response_model=ChangeRequestOut)
async def approve_change_request(
    id: str, request: Request, use_cases: UseCases = Depends(get_use_cases)
) -> ChangeRequestOut:
    return to_out(use_cases.approve(bearer_token(request), id, await json_body(request)))


@router.post("/change-requests/{id}/request-changes", response_model=ChangeRequestOut)
async def request_changes_on_change_request(
    id: str, request: Request, use_cases: UseCases = Depends(get_use_cases)
) -> ChangeRequestOut:
    return to_out(
        use_cases.request_changes(bearer_token(request), id, await json_body(request))
    )
