# Data Model: Change Request Workflow (First Version)

**Feature**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Date**: 2026-11-17

## Domain concepts

### Role

`Requester` | `Reviewer`. A user holds zero, one or both.

### Actor

The authenticated caller of one operation: `user_id` plus the set of roles read from storage
**at the start of that operation** (FR-013, FR-023). Never cached across operations.

### Status

`Draft` | `PendingReview` | `ChangesRequested` | `Approved` (FR-002). `Approved` is the only
terminal status (FR-017).

### ChangeRequest (entity)

| Field | Type | Rules |
|-------|------|-------|
| `id` | integer | Assigned by storage on create; unique; never reused |
| `title` | text | Non-blank (not empty after trimming whitespace); ≤ 200 characters (A6, open assumption) |
| `description` | text | Non-blank; ≤ 10,000 characters (A6) |
| `reason` | text | Non-blank; ≤ 10,000 characters (A6) |
| `requester_id` | user id | The creating user; never changes (FR-005, FR-023) |
| `status` | Status | Starts as `Draft`; changes only via the transitions below |
| `version` | integer ≥ 1 | 1 on create; +1 on every successful modification (FR-001, FR-014) |
| `changes_requested_reason` | text or null | Set by RequestChanges (non-blank, ≤ 10,000 characters); holds only the most recent reason (FR-011); null until the first RequestChanges |

Values are stored as given (not trimmed); "non-blank" is only a check. Lengths are counted in
characters (Unicode code points).

## State transitions (single source of truth: Domain)

| From | Operation | To | Who (permission, FR-020 step 3) |
|------|-----------|----|----------------------------------|
| — | Create | Draft | Holds Requester |
| Draft | Edit | Draft | Is requester **and** holds Requester |
| ChangesRequested | Edit | ChangesRequested | Is requester **and** holds Requester |
| Draft | Submit | PendingReview | Is requester **and** holds Requester |
| ChangesRequested | Submit | PendingReview | Is requester **and** holds Requester |
| PendingReview | Approve | Approved | Holds Reviewer **and** is not requester (FR-012) |
| PendingReview | RequestChanges | ChangesRequested | Holds Reviewer **and** is not requester (FR-016) |

Every other (status, operation) pair is rejected as `invalid_status` (FR-003). There is no
delete operation (FR-021). Edit replaces all three text fields (plan assumption PA-4).

## Visibility (FR-015)

| Caller | Can see |
|--------|---------|
| Holds Reviewer | All requests |
| Holds Requester only | Requests where `requester_id` = caller |
| Holds no role | Nothing (list is empty; single request is `not_found`) |

A request the caller cannot see is reported as `not_found` for every operation.

## Order of checks for state-changing operations (FR-020)

1. Identity — token missing or unknown → `unauthenticated` *(Application)*
2. Existence and visibility — id unknown, non-numeric, or not visible → `not_found`
   *(Application loads; Domain visibility rule decides)*
3. Permission — table above → `forbidden` *(Domain)*
4. Input validity — body not a JSON object, missing/invalid `version`, invalid fields →
   `invalid_input` *(Domain)*
5. Version — `version` ≠ stored version → `conflict` *(Domain)*
6. Status — transition not allowed from current status → `invalid_status` *(Domain)*
7. Write — conditional update on the loaded version; zero rows matched → `conflict`
   *(Infrastructure, reported via Application)*

Create runs steps 1, 3 and 4 only. View and list run steps 1–2 only.

`version` is valid only if it is a JSON integer ≥ 1 (booleans and strings are invalid).

## Storage schema (SQLite)

```text
users
  id          TEXT PRIMARY KEY            -- e.g. "alice"
  token_hash  TEXT NOT NULL UNIQUE        -- SHA-256 hex of the bearer token (R3)

user_roles
  user_id     TEXT NOT NULL REFERENCES users(id)
  role        TEXT NOT NULL CHECK (role IN ('requester', 'reviewer'))
  PRIMARY KEY (user_id, role)

change_requests
  id                        INTEGER PRIMARY KEY AUTOINCREMENT
  title                     TEXT NOT NULL
  description               TEXT NOT NULL
  reason                    TEXT NOT NULL
  requester_id              TEXT NOT NULL REFERENCES users(id)
  status                    TEXT NOT NULL CHECK (status IN
                              ('Draft', 'PendingReview', 'ChangesRequested', 'Approved'))
  version                   INTEGER NOT NULL CHECK (version >= 1)
  changes_requested_reason  TEXT NULL
```

The `CHECK` on `status` makes a status outside the workflow impossible to store (SC-006). The
write for every modification is a single conditional statement (R2):

```text
UPDATE change_requests SET <new values>, version = version + 1
WHERE id = :id AND version = :loaded_version
```

## Ports (Application layer, `typing.Protocol`)

| Port | Operations | Implemented by |
|------|------------|----------------|
| `ChangeRequestRepository` | get by id; add (returns stored request with id and version 1); update if version matches (returns whether a row was updated); list all; list by requester | SQLite adapter |
| `UserDirectory` | find actor (user id + current roles) by bearer token | SQLite adapter |
