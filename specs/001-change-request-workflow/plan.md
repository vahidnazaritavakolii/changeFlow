# Implementation Plan: Change Request Workflow (First Version)

**Branch**: none created (work is on `main`; feature directory `specs/001-change-request-workflow`)
| **Date**: 2026-11-17 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/001-change-request-workflow/spec.md`

## Summary

ChangeFlow v1 is an HTTP API through which Requesters create, edit and submit change requests
and Reviewers approve them or return them for changes. Nobody may approve or return their own
request. The workflow, the self-review rules, visibility, input validation and the fixed order
of checks (FR-020) live in a pure-Python Domain package with unit tests. Thin Application use
cases authenticate the caller, load the request, apply the Domain rules and save. Persistence
is SQLite through the standard library, with optimistic locking: a `version` column and an atomic
conditional update, so stale writes are rejected with `409 conflict`. FastAPI handlers only parse
the request, call one use case and map the outcome to a status code.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: FastAPI and uvicorn (runtime); pytest and httpx (tests). No ORM
(research R1, R9)

**Storage**: SQLite file via stdlib `sqlite3` (research R1)

**Testing**: pytest. Domain unit tests without HTTP or database; HTTP tests via FastAPI
`TestClient` against a temporary SQLite file, verifying persisted rows; repository integration
tests for the conditional update; an AST-based architecture test (research R7)

**Target Platform**: Linux server (also runs on macOS for development)

**Project Type**: web service (HTTP API only, no UI)

**Performance Goals**: none for this version (SC-006/A8 removed in clarification; performance
targets are out of scope)

**Constraints**: FR-020 check order; stale writes rejected atomically (FR-014); no status outside
the workflow (SC-006); identity and current roles checked on every operation (FR-013)

**Scale/Scope**: internal company tool; 7 endpoints; 1 business table plus 2 identity tables

No open NEEDS CLARIFICATION items remain. Spec assumptions A6 (field limits) and A7 (identity
mechanism) remain open reviewable assumptions; A7 is covered for this version by research R3.

## Constitution Check (pre-research gate)

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Requirement | Pre-research status |
|-----------|-------------|---------------------|
| I. Separation (NON-NEGOTIABLE) | Business rules only in Domain/Application; handlers parse → one use case → map; no status, ownership or role conditions in handlers; Domain free of HTTP and persistence | PASS (planned): Domain package for rules; use cases per operation; enforced by architecture test |
| II. Security by default | Identity, current permission and current status verified before any change; deny by default; no-self-review in Domain | PASS (planned): auth is step 1 of every use case; roles read per operation; FR-012/FR-016 in Domain |
| III. Integrity under concurrency | Stale writes rejected with explicit conflict; never outside workflow | PASS (planned): R2 decides the mechanism |
| IV. Evidence-based quality | Domain unit tests without HTTP/DB; every transition and authorization rule tested; sensitive tests verify persisted state; only real results reported | PASS (planned): test layout below; quickstart marked "planned" |
| V. Simplicity | No layer, abstraction or dependency without a present, documented need; nothing beyond scope | PASS (planned): R8 justifies each layer; no ORM, DI container or fakes |
| VI. Traceable decisions | Unstated product behaviour clarified or recorded as an assumption; technology justified in research | PASS (planned): R1–R9; planning assumptions PA-1…PA-6 below |

No violations, so Complexity Tracking stays empty.

## Project Structure

### Documentation (this feature)

```text
specs/001-change-request-workflow/
├── spec.md
├── plan.md              # this file
├── research.md          # Phase 0
├── data-model.md        # Phase 1
├── quickstart.md        # Phase 1
├── contracts/
│   └── http-api.md      # Phase 1
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 (/speckit-tasks, not created here)
```

### Source Code (repository root)

```text
pyproject.toml
src/changeflow/
├── __init__.py
├── domain/
│   ├── __init__.py
│   ├── model.py          # Role, Status, Actor, ChangeRequest; transition table
│   ├── rules.py          # visibility rule (FR-020 step 2) and checks 3–6 in order;
│   │                     # create/edit/submit/approve/request_changes return the new
│   │                     # ChangeRequest
│   └── errors.py         # NotFound, Forbidden, InvalidInput, Conflict, InvalidStatus
├── application/
│   ├── __init__.py
│   ├── ports.py          # ChangeRequestRepository, UserDirectory (typing.Protocol)
│   ├── errors.py         # Unauthenticated
│   └── use_cases.py      # one function per operation: authenticate → load → domain → save
├── infrastructure/
│   ├── __init__.py
│   ├── sqlite_db.py      # connect (foreign_keys, busy_timeout), idempotent schema
│   ├── sqlite_repository.py
│   ├── sqlite_users.py   # token hash lookup + current roles
│   └── seed.py           # dev-only: create users/roles, print tokens as export lines
└── api/
    ├── __init__.py
    ├── app.py            # create_app(db_path): wiring (composition root) + error handler
    ├── routes.py         # handlers: parse → one use case → response
    ├── http_io.py        # bearer-token and JSON-body parsing helpers (no business rules)
    ├── errors.py         # outcome → (status, code) table (contract)
    └── schemas.py        # response models (output only)

tests/
├── conftest.py           # temp SQLite file, seeded users, TestClient, direct-DB reader
├── unit/domain/          # transitions, permissions, self-review, validation, check order
├── integration/          # SQLite repository: conditional update, interleaving, CHECK on status
├── api/                  # one module per user story; asserts response AND persisted row
└── architecture/
    └── test_architecture.py   # research R7
```

**Structure Decision**: a single Python project with a `src/` layout and four packages,
matching the four responsibilities required by Principle I. Each package is justified in
research R8; there are no further sub-layers. Dependencies point inward: `api` →
`application` → `domain`; `infrastructure` → `application` (implements its ports) and `domain`.
Only `api/app.py` imports `infrastructure`, to wire the adapters.

### How each layer satisfies Principle I

- **Domain**: owns statuses, the transition table, the visibility rule, the permission rules
  (including no self-approval and no self-RequestChanges), field validation (A6 limits) and
  checks 3–6 of FR-020 in order. It imports only the standard library.
- **Application**: for each operation, it (1) authenticates via `UserDirectory`, (2) parses the
  id and loads via `ChangeRequestRepository`, raising `NotFound` when the Domain visibility rule
  says so, (3) calls the Domain function, (4) persists with the conditional update and turns a
  zero-row result into `Conflict`. It contains no business conditions of its own beyond this
  orchestration.
- **API**: each handler extracts the bearer token, path id and raw JSON body with `http_io`,
  calls exactly one use case and returns its result. A single exception handler maps outcome
  errors to the status codes in [contracts/http-api.md](./contracts/http-api.md) through a
  lookup table.

## Testing strategy (Principle IV)

| Test group | What it proves | Spec coverage |
|------------|----------------|---------------|
| `tests/unit/domain` (no HTTP, no DB) | Every allowed transition; every disallowed (status, operation) pair → invalid status; permission matrix per role/ownership; self-approval and self-RequestChanges forbidden for dual-role users; validation (blank, A6 limits, `version` type); FR-020 order with combined failures | FR-002–FR-012, FR-016, FR-017, FR-019, FR-020, SC-001, SC-004 |
| `tests/integration` (SQLite) | Conditional update succeeds once and fails with stale version; interleaving test; `CHECK` rejects an unknown status | FR-014, SC-002, SC-006 |
| `tests/api` (HTTP + SQLite) | Each acceptance scenario of User Stories 1–4 and each edge case, asserting status code, error `code` **and** the stored row (unchanged after every rejection) | All scenarios, FR-013, FR-015, FR-018, FR-021–FR-023, SC-003, SC-005 |
| `tests/architecture` | No forbidden imports in Domain or Application; handlers have no branching, no business names, and exactly one use-case call | Principle I |

Role removal (FR-023) is tested by deleting a `user_roles` row between operations.

## Planning assumptions (Principle VI — reviewable)

Product behaviour the spec does not state, needed to build the API. Each item is a
**reviewable assumption**, not a product decision:

- **PA-1**: `changes_requested_reason` is kept after resubmission and after approval (it is
  "the most recent reason") until a new RequestChanges replaces it.
- **PA-2**: The list returns all visible requests ordered by `id`, with no pagination or
  filtering (no requirement asks for them).
- **PA-3**: An authenticated user with no role gets an empty list (consistent with FR-015(c)).
- **PA-4**: Edit replaces title, description and reason together; all three are required.
- **PA-5**: "Non-blank" means not empty after trimming whitespace; values are stored as given.
- **PA-6**: A non-numeric request id is reported as `not_found` (after authentication).

## Constitution Check (post-design re-evaluation)

| Principle | Evidence in design | Status |
|-----------|--------------------|--------|
| I | Rules in `domain/rules.py`; handlers limited to parse/one call/map and checked by R7 test; Domain imports only stdlib; Application depends on ports, not SQLite | PASS |
| II | Bearer token verified and roles re-read in every use case (R3); visibility and default denial in Domain; FR-012/FR-016 enforced in Domain for every entry point | PASS. The role-removal race window is documented in R3 as a v1 simplification |
| III | Version compared in Domain plus atomic `UPDATE … WHERE version = ?` (R2); `CHECK` constraint on status; no partial writes (single statement) | PASS |
| IV | Unit tests without HTTP/DB; per-transition and per-rule tests; API tests read the stored row; deterministic SC-002 tests; quickstart states that only real runs count | PASS |
| V | Four packages and two ports, each with a present need (R8); dependencies limited to FastAPI, uvicorn, pytest, httpx; no rejection, cancellation, deletion, pagination or audit features | PASS |
| VI | Technology choices R1–R9 in research; unstated behaviour recorded as PA-1…PA-6; spec A6/A7 kept open | PASS |

## Complexity Tracking

No constitution violations; nothing to justify.
