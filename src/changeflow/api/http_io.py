"""HTTP parsing helpers. Parsing only; no business rules (research R5)."""

import json

from fastapi import Request

# Marker for a body that is empty or not valid JSON. The Domain rejects any
# non-object body as invalid input at FR-020 step 4.
INVALID_BODY = object()


def bearer_token(request: Request) -> str | None:
    header = request.headers.get("authorization")
    if header is None:
        return None
    scheme, _, value = header.partition(" ")
    if scheme.lower() != "bearer" or not value.strip():
        return None
    return value.strip()


async def json_body(request: Request) -> object:
    raw = await request.body()
    if not raw:
        return INVALID_BODY
    try:
        return json.loads(raw)
    except (ValueError, UnicodeDecodeError):
        return INVALID_BODY
