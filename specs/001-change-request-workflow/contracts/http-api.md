# HTTP Contract: ChangeFlow Change Requests (v1)

**Feature**: [spec.md](../spec.md) | **Data model**: [data-model.md](../data-model.md)

All requests and responses use `application/json`. Every endpoint requires
`Authorization: Bearer <token>`.

## Outcome categories → HTTP status (FR-018, research R6)

| Outcome | Status | `code` | When (FR-020 order) |
|---------|--------|--------|---------------------|
| success (created) | 201 | — | Create succeeded |
| success | 200 | — | Any other operation succeeded |
| unauthenticated | 401 | `unauthenticated` | Step 1: token missing, malformed or unknown. Response has `WWW-Authenticate: Bearer` |
| not found | 404 | `not_found` | Step 2: id unknown, non-numeric, or request not visible to the caller |
| forbidden | 403 | `forbidden` | Step 3: missing role, not the owner, self-approval, self-RequestChanges |
| invalid input | 400 | `invalid_input` | Step 4: body not a JSON object; `version` missing or not an integer ≥ 1; text field missing, blank or too long |
| conflict | 409 | `conflict` | Step 5/7: `version` is not the current version, or the request changed before the write |
| invalid status | 422 | `invalid_status` | Step 6: operation not allowed in the request's current status |

Only the first failing check is reported. Any rejected operation leaves the stored request
unchanged.

### Error body

```json
{ "error": { "code": "conflict", "message": "Human-readable explanation." } }
```

`code` is one of the six values above; `message` is informational and may change.

## Resource representation

```json
{
  "id": 42,
  "title": "Add export endpoint",
  "description": "Expose change requests as CSV.",
  "reason": "Auditors need offline copies.",
  "requester_id": "alice",
  "status": "Draft",
  "version": 1,
  "changes_requested_reason": null
}
```

`status` ∈ `Draft`, `PendingReview`, `ChangesRequested`, `Approved`.

## Endpoints

### `POST /change-requests` — Create (FR-005)

Body: `{ "title": str, "description": str, "reason": str }`

- 201: the created request (`status` = `Draft`, `version` = 1).
- Possible errors: 401, 403 (no Requester role), 400.

### `GET /change-requests` — List (FR-015)

- 200: `{ "items": [ <request>, … ] }`, ordered by `id` ascending. Reviewers get all requests;
  Requester-only callers get their own; callers with no role get an empty list.
- Possible errors: 401.

### `GET /change-requests/{id}` — View (FR-015)

- 200: the request.
- Possible errors: 401, 404.

### `PUT /change-requests/{id}` — Edit (FR-006, FR-008, FR-009)

Body: `{ "title": str, "description": str, "reason": str, "version": int }`

- 200: the updated request (`version` incremented, `status` unchanged).
- Possible errors: 401, 404, 403 (not owner or no Requester role), 400, 409, 422 (status
  PendingReview or Approved).

### `POST /change-requests/{id}/submit` — Submit (FR-007)

Body: `{ "version": int }`

- 200: the request with `status` = `PendingReview`.
- Possible errors: 401, 404, 403, 400, 409, 422 (status PendingReview or Approved).

### `POST /change-requests/{id}/approve` — Approve (FR-010, FR-012)

Body: `{ "version": int }`

- 200: the request with `status` = `Approved`.
- Possible errors: 401, 404, 403 (no Reviewer role, or caller is the requester), 400, 409, 422
  (status not PendingReview).

### `POST /change-requests/{id}/request-changes` — Request changes (FR-011, FR-016)

Body: `{ "version": int, "reason": str }`

- 200: the request with `status` = `ChangesRequested` and `changes_requested_reason` set.
- Possible errors: 401, 404, 403 (no Reviewer role, or caller is the requester), 400 (missing,
  blank or too long `reason`), 409, 422 (status not PendingReview).

### Not provided (by specification)

No delete (FR-021), reject or cancel (FR-017) endpoints, and no user or role administration.
Any other method or path returns the framework's default 404/405.

## Worked examples of check order (FR-020)

| Situation | Result |
|-----------|--------|
| No token, unknown id | 401 |
| Requester-only user B edits A's request, invalid body | 404 |
| Reviewer approves own request with an outdated version | 403 |
| Owner edits with blank title and outdated version | 400 |
| Owner submits an already-submitted request with the old version | 409 |
| Owner submits an already-submitted request with the current version | 422 |
