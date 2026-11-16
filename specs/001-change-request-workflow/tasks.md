---

description: "Task list for ChangeFlow change request workflow (first version)"
---

# Tasks: Change Request Workflow (First Version)

**Input**: Design documents from `specs/001-change-request-workflow/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md),
[data-model.md](./data-model.md), [contracts/http-api.md](./contracts/http-api.md),
[quickstart.md](./quickstart.md)

**Tests**: Required. Constitution Principle IV requires tests for every state transition and
authorization rule, and the user asked for tests before implementation in every story. Write each
story's test tasks first and confirm they fail (or, for verification stories, record that they
pass) before the implementation tasks.

**Organization**: Tasks are grouped by user story in spec priority order: US1 (P1), US2 (P2),
US3 (P2), US4 (P3).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel with the other [P] tasks of the same phase: it touches a file that
  no other task in that phase touches, and it does not depend on an unfinished task in the phase.
- **[Story]**: The user story the task belongs to (US1–US4).
- Paths are relative to the repository root (single project, `src/` layout, per plan.md).

## Shared conventions (apply to every task)

- Outcome errors: Domain raises `NotFound`, `Forbidden`, `InvalidInput`, `Conflict`,
  `InvalidStatus` from `src/changeflow/domain/errors.py`; Application raises `Unauthenticated`
  from `src/changeflow/application/errors.py`. HTTP mapping (contract): 401 `unauthenticated`,
  404 `not_found`, 403 `forbidden`, 400 `invalid_input`, 409 `conflict`, 422 `invalid_status`.
- Check order for state-changing operations (FR-020): (1) identity → (2) existence/visibility →
  (3) permission → (4) input validity incl. `version` → (5) version → (6) status → (7)
  conditional write. Create: 1, 3, 4. View/list: 1, 2.
- Every HTTP test of a rejected operation asserts the status code, the error `code`, **and** that
  the stored row (read directly from SQLite via the `read_row` fixture) is identical before and
  after (SC-003).
- Test users (seeded by `tests/conftest.py`): `alice` = requester; `bob` = reviewer; `erin` =
  reviewer; `carol` = requester + reviewer; `dave` = no roles.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization

- [X] T001 Create `pyproject.toml`: project name `changeflow`, `requires-python = ">=3.12"`,
  `src/` layout (setuptools, package dir `src`), runtime dependencies `fastapi>=0.115` and
  `uvicorn>=0.30`, optional `dev` extra with `pytest>=8` and `httpx>=0.27`, and
  `[tool.pytest.ini_options]` with `testpaths = ["tests"]` and
  `addopts = "--import-mode=importlib"` (research R9)
- [X] T002 [P] Create empty package markers `src/changeflow/__init__.py`,
  `src/changeflow/domain/__init__.py`, `src/changeflow/application/__init__.py`,
  `src/changeflow/infrastructure/__init__.py`, `src/changeflow/api/__init__.py`
- [X] T003 [P] Create `.gitignore` ignoring `.venv/`, `__pycache__/`, `*.pyc`, `.pytest_cache/`,
  `*.egg-info/`, `changeflow.db`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Domain model, schema, identity, shared test fixtures, HTTP skeleton and the
architecture test. Schema creation (T011) and shared fixtures (T013) come before every task that
reads or writes data.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

### Tests first (Domain foundation)

- [ ] T004 [P] Write `tests/unit/domain/test_model.py` (no HTTP, no DB): `Status` has exactly the
  values `Draft`, `PendingReview`, `ChangesRequested`, `Approved`; `Role` has exactly
  `requester`, `reviewer`; the transition table contains exactly these (from-status, operation)
  → to-status entries: (Draft, edit) → Draft, (ChangesRequested, edit) → ChangesRequested,
  (Draft, submit) → PendingReview, (ChangesRequested, submit) → PendingReview,
  (PendingReview, approve) → Approved, (PendingReview, request_changes) → ChangesRequested; no
  entry starts from Approved; there is no delete operation (FR-002, FR-017, FR-021)
- [ ] T005 [P] Write `tests/unit/domain/test_rules_common.py` (no HTTP, no DB) for the shared
  rules: visibility (FR-015) — the owner sees their own request with any roles or none
  (including an owner with no roles), a reviewer sees any request, a requester-only non-owner
  and a no-role non-owner see nothing; text validation (FR-004, A6,
  PA-5) — title "Non-blank (not empty after trimming whitespace); ≤ 200 characters", description
  and reason "Non-blank; ≤ 10,000 characters", 200/10,000 accepted and 201/10,001 rejected,
  whitespace-only rejected, missing key rejected, non-string rejected, values returned unchanged
  (not trimmed); version validation — "valid only if it is a JSON integer ≥ 1 (booleans and
  strings are invalid)": `1` valid; missing, `0`, `-1`, `"1"`, `true`, `1.0`, `null` →
  `InvalidInput`; a body that is not a JSON object → `InvalidInput`

### Domain and Application foundation

- [ ] T006 [P] Create `src/changeflow/domain/errors.py`: base `DomainError(Exception)` with a
  `message` attribute, and subclasses `NotFound`, `Forbidden`, `InvalidInput`, `Conflict`,
  `InvalidStatus`
- [ ] T007 [P] Create `src/changeflow/application/errors.py`: `Unauthenticated(Exception)` with a
  `message` attribute
- [ ] T008 Create `src/changeflow/domain/model.py` (stdlib only): `Role` enum (`requester`,
  `reviewer`); `Status` enum (`Draft`, `PendingReview`, `ChangesRequested`, `Approved`); frozen
  dataclass `Actor(user_id: str, roles: frozenset[Role])`; frozen dataclass `ChangeRequest` with
  fields `id: int | None`, `title`, `description`, `reason`, `requester_id: str`,
  `status: Status`, `version: int` ("integer ≥ 1; 1 on create; +1 on every successful
  modification"), `changes_requested_reason: str | None` ("holds only the most recent reason";
  null until the first RequestChanges); module constant `TRANSITIONS` mapping
  (Status, operation name) → Status exactly as listed in T004. Make T004 pass
- [ ] T009 Create `src/changeflow/domain/rules.py` with the shared rules only: `is_visible(actor,
  request) -> bool` (FR-015 table in data-model.md); `validate_body(body) -> dict` (raises
  `InvalidInput` if `body` is not a `dict`); `validate_text(body, *field_names)` using limits
  defined once as module-level constants in `rules.py` (A6: `title` ≤ 200, `description` ≤
  10,000, `reason` ≤ 10,000), non-blank after `strip()`, values
  returned as given; `validate_version(body) -> int` (JSON integer ≥ 1, reject `bool`);
  `check_version(request, version)` raising `Conflict` when they differ;
  `next_status(request, operation)` raising `InvalidStatus` when (status, operation) is not in
  `TRANSITIONS`. Make T005 pass
- [ ] T010 Create `src/changeflow/application/ports.py` with `typing.Protocol` classes:
  `ChangeRequestRepository` (`get(id: int) -> ChangeRequest | None`;
  `add(request: ChangeRequest) -> ChangeRequest` returning it with assigned `id` and
  `version = 1`; `update_if_version(request: ChangeRequest, expected_version: int) -> bool`;
  `list_all() -> list[ChangeRequest]`; `list_by_requester(user_id: str) -> list[ChangeRequest]`)
  and `UserDirectory` (`find_actor_by_token(token: str) -> Actor | None`) (data-model.md, ports)

### Schema, provisioning and shared fixtures

- [ ] T011 Create `src/changeflow/infrastructure/sqlite_db.py`: `connect(db_path) ->
  sqlite3.Connection` (sets `PRAGMA foreign_keys = ON`, `timeout=5.0`/busy timeout 5 s,
  `row_factory = sqlite3.Row`); `init_schema(db_path)` running idempotent
  `CREATE TABLE IF NOT EXISTS` for `users(id TEXT PRIMARY KEY, token_hash TEXT NOT NULL UNIQUE)`,
  `user_roles(user_id TEXT NOT NULL REFERENCES users(id), role TEXT NOT NULL CHECK (role IN
  ('requester', 'reviewer')), PRIMARY KEY (user_id, role))` and `change_requests(id INTEGER
  PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, description TEXT NOT NULL, reason TEXT NOT
  NULL, requester_id TEXT NOT NULL REFERENCES users(id), status TEXT NOT NULL CHECK (status IN
  ('Draft', 'PendingReview', 'ChangesRequested', 'Approved')), version INTEGER NOT NULL CHECK
  (version >= 1), changes_requested_reason TEXT NULL)`; `hash_token(token) -> str` (SHA-256 hex)
  (data-model.md storage schema, research R1/R3)
- [ ] T012 Create `src/changeflow/infrastructure/seed.py` (development only): function
  `create_user(db_path, user_id, roles) -> str` that calls `init_schema`, generates a token with
  `secrets.token_urlsafe(32)`, stores only `hash_token(token)` and the roles, and returns the
  token; `main()` CLI run as `python -m changeflow.infrastructure.seed --db PATH user=role[,role]
  …` printing one line per user: `export <USER_ID_UPPERCASE>_TOKEN=<token>` (quickstart.md)
- [ ] T013 Create `tests/conftest.py` shared fixtures: `db_path` (fresh SQLite file under
  `tmp_path`, schema initialised); `tokens` (dict user → token created with `create_user` for
  alice/bob/erin/carol/dave as in Shared conventions); `auth(user)` → `{"Authorization":
  "Bearer <token>"}`; `client` (FastAPI `TestClient(create_app(db_path))`, importing `create_app`
  inside the fixture); `read_row(id)` → dict of the stored `change_requests` row or `None`,
  read with a direct `sqlite3` connection; `insert_request(requester_id, status="Draft",
  version=1, title="T", description="D", reason="R", changes_requested_reason=None) -> int`
  inserting directly with SQL so each story can start from any status; `remove_role(user_id,
  role)` deleting a `user_roles` row

### Infrastructure (tests first)

- [ ] T014 [P] Write `tests/integration/test_sqlite_repository.py` against a real temp SQLite file
  (uses `db_path`, `insert_request`, `read_row`): `add` assigns increasing ids and `version` 1;
  `get` returns `None` for an unknown id; `list_all` and `list_by_requester` return requests
  ordered by `id` (PA-2); `update_if_version` with the current version writes all fields,
  increments `version` by exactly 1 and returns `True`; with any other version returns `False`
  and the row is unchanged; inserting or updating to status `'Rejected'` raises
  `sqlite3.IntegrityError` (CHECK constraint, SC-006)
- [ ] T015 [P] Write `tests/integration/test_sqlite_users.py`: a valid token returns
  `Actor(user_id, roles)` with the user's current roles; an unknown token returns `None`; only the
  hash is stored (the raw token does not appear in `users`); after `remove_role` the next lookup
  no longer contains that role (FR-023)
- [ ] T016 [P] Create `src/changeflow/infrastructure/sqlite_repository.py`:
  `SqliteChangeRequestRepository(db_path)` implementing `ChangeRequestRepository`; one connection
  per call; `update_if_version` is the single statement `UPDATE change_requests SET title = ?,
  description = ?, reason = ?, status = ?, changes_requested_reason = ?, version = version + 1
  WHERE id = ? AND version = ?` returning `cursor.rowcount == 1` (research R2). Make T014 pass
- [ ] T017 [P] Create `src/changeflow/infrastructure/sqlite_users.py`:
  `SqliteUserDirectory(db_path)` implementing `UserDirectory`; looks up `hash_token(token)` and
  reads roles from `user_roles` on every call (no caching). Make T015 pass

### Application and HTTP skeleton

- [ ] T018 Create `src/changeflow/application/use_cases.py` with class `UseCases(repository,
  users)` and private helpers only: `_authenticate(token: str | None) -> Actor` (raises
  `Unauthenticated` for `None`, empty or unknown token — FR-020 step 1);
  `_load_visible(actor, raw_id: str) -> ChangeRequest` (non-numeric id, unknown id or
  `not is_visible(...)` → `NotFound`, PA-6 — step 2); `_save(updated, loaded_version) ->
  ChangeRequest` (calls `update_if_version`; `False` → `Conflict`; returns the updated request
  with `version = loaded_version + 1` — step 7). Imports only `changeflow.domain` and
  `changeflow.application`
- [ ] T019 [P] Create `src/changeflow/api/http_io.py` (parsing only, no business rules):
  `bearer_token(request) -> str | None` (value after `Bearer ` in `Authorization`, else `None`);
  `async json_body(request) -> object` (parsed JSON, or the sentinel `INVALID_BODY` when the body
  is empty or not valid JSON) (research R5)
- [ ] T020 [P] Create `src/changeflow/api/errors.py`: dict `ERROR_MAP` from exception class to
  `(status, code)`: `Unauthenticated` → (401, `unauthenticated`), `NotFound` → (404,
  `not_found`), `Forbidden` → (403, `forbidden`), `InvalidInput` → (400, `invalid_input`),
  `Conflict` → (409, `conflict`), `InvalidStatus` → (422, `invalid_status`); exception handler
  returning `{"error": {"code": ..., "message": ...}}` and, for 401, header
  `WWW-Authenticate: Bearer` (contracts/http-api.md, research R6)
- [ ] T021 [P] Create `src/changeflow/api/schemas.py` (output only): Pydantic models
  `ChangeRequestOut` (`id`, `title`, `description`, `reason`, `requester_id`, `status`,
  `version`, `changes_requested_reason`), `ChangeRequestList(items: list[ChangeRequestOut])`,
  and a `to_out(request)` converter
- [ ] T022 Create `src/changeflow/api/routes.py` with an empty `APIRouter` named `router` and a
  dependency `get_use_cases(request)` returning `request.app.state.use_cases`
- [ ] T023 Create `src/changeflow/api/app.py`: `create_app(db_path: str | None = None)` (default
  from env `CHANGEFLOW_DB`, else `changeflow.db`) that calls `init_schema`, builds
  `UseCases(SqliteChangeRequestRepository(db_path), SqliteUserDirectory(db_path))`, stores it on
  `app.state.use_cases`, includes `router`, and registers the `api/errors.py` handler for every
  class in `ERROR_MAP` (composition root, plan.md)
- [ ] T024 Write `tests/architecture/test_architecture.py` using stdlib `ast` (research R7):
  (a) no module under `src/changeflow/domain/` imports `fastapi`, `starlette`, `pydantic`,
  `sqlite3`, `sqlalchemy`, `httpx`, `uvicorn`, `changeflow.application`,
  `changeflow.infrastructure` or `changeflow.api`; (b) no module under
  `src/changeflow/application/` imports `fastapi`, `starlette`, `sqlite3`, `sqlalchemy`,
  `uvicorn`, `changeflow.infrastructure` or `changeflow.api`; (c) every function in
  `src/changeflow/api/routes.py` decorated with `router.get/post/put/patch/delete` contains no
  `If`, `IfExp`, `Match`, `While`, `For`, `BoolOp` or `Compare` node, no reference to the names
  `Status`, `Role`, `requester_id` or `roles`, and exactly one call whose function is an
  attribute of the `UseCases` dependency parameter; (d) a self-test asserting the checker flags
  a sample handler source that contains an `if` on `status`, so the check cannot pass vacuously

**Checkpoint**: `pytest tests/unit tests/integration tests/architecture` passes.

---

## Phase 3: User Story 1 — Create, edit and submit a change request (Priority: P1) 🎯 MVP

**Goal**: A Requester creates a Draft, views and lists their requests, edits the Draft and
submits it to PendingReview; visibility and ownership are enforced.

**Independent Test**: Alice creates, edits, submits and reads back a request; the stored row has
the last edit and status PendingReview (spec US1).

### Tests for User Story 1 (write first, confirm they fail) ⚠️

- [ ] T025 [P] [US1] Write `tests/unit/domain/test_us1_requester_rules.py` (no HTTP, no DB):
  `create` — Requester gets a Draft with `requester_id` = caller and `version` 1; no Requester
  role (reviewer-only, no roles) → `Forbidden` (also when the body is invalid: forbidden before
  invalid input); `edit` and `submit` on own Draft succeed (edit keeps status Draft, submit →
  PendingReview); non-owner with Requester role, owner who lost the Requester role (still able
  to view it, FR-015), and reviewer-only caller → `Forbidden`; edit on PendingReview or Approved → `InvalidStatus`;
  submit on PendingReview or Approved → `InvalidStatus`; stale `version` → `Conflict`; order
  checks: forbidden beats invalid input, invalid input beats conflict, conflict beats invalid
  status (FR-005–FR-009, FR-019, FR-020)
- [ ] T026 [P] [US1] Write `tests/api/test_us1_create_view_list.py` (HTTP + SQLite): US1
  scenario 1 (201, row stored as Draft/version 1/requester alice); scenario 4 (bob, dave → 403,
  no row stored); scenario 5 (missing/blank/too-long fields → 400, no row stored); scenario 7
  (no token, malformed header, unknown token → 401 with `WWW-Authenticate: Bearer` on create,
  list and view); view own request → 200; scenario 9 (alice lists only hers; bob and carol list
  all; dave gets `{"items": []}`, PA-3); unknown id and non-numeric id → 404; alice viewing a
  request owned by carol → 404 (hiding existence, FR-015); `DELETE /change-requests/{id}` and an
  unlisted route (e.g. `POST /change-requests/{id}/reject`) → 404 or 405, with the stored row
  unchanged (FR-019, FR-021)
- [ ] T027 [P] [US1] Write `tests/api/test_us1_edit_submit.py` (HTTP + SQLite): scenario 2 (PUT
  with current version → 200, row has new text, version +1); scenario 3 (submit → 200,
  PendingReview); scenario 6 (alice edits/submits carol's Draft → 404; bob (reviewer) edits or
  submits alice's Draft → 403); scenario 8 (edit when PendingReview or Approved → 422); missing
  `version` → 400; non-JSON body → 400; repeated submit with old version → 409 and with current
  version → 422 (FR-022); an edit with values identical to the stored ones → 200 and version
  +1 (edge case); an edit body with an unknown extra field → 200, the field ignored and not
  stored (PA-7); after every rejection the row is unchanged (SC-003)

### Implementation for User Story 1

- [ ] T028 [US1] Add `create_request(actor, body)`, `edit(actor, request, body)` and
  `submit(actor, request, body)` to `src/changeflow/domain/rules.py`, each applying FR-020 steps
  3→6 in order using the shared helpers: permission (create: holds Requester; edit/submit: is
  requester **and** holds Requester) → `validate_body`/`validate_text("title", "description",
  "reason")` (edit, create) / `validate_version` (edit, submit) → `check_version` →
  `next_status`; return the new `ChangeRequest` (edit replaces all three fields, PA-4; neither
  clears `changes_requested_reason`, PA-1). Make T025 pass
- [ ] T029 [US1] Add `UseCases.create(token, body)`, `get(token, raw_id)`, `list_requests(token)`,
  `edit(token, raw_id, body)` and `submit(token, raw_id, body)` to
  `src/changeflow/application/use_cases.py`: authenticate → (load visible) → Domain function →
  `repository.add` / `_save`; `list_requests` returns `list_all()` for reviewers, else
  `list_by_requester(actor.user_id)` for every other caller, whatever roles they hold (empty if
  they own none) (FR-015, PA-2, PA-3)
- [ ] T030 [US1] Add handlers to `src/changeflow/api/routes.py`: `POST /change-requests` (201),
  `GET /change-requests`, `GET /change-requests/{id}`, `PUT /change-requests/{id}`,
  `POST /change-requests/{id}/submit`; each handler reads `bearer_token`, the path id as `str`,
  and `json_body` where applicable, calls exactly one `UseCases` method and returns `to_out(...)`
  (or `ChangeRequestList`). No conditions (T024). Make T026, T027 and T024 pass

**Checkpoint**: `pytest tests/unit tests/integration tests/api/test_us1_create_view_list.py
tests/api/test_us1_edit_submit.py tests/architecture` passes. MVP is usable.

---

## Phase 4: User Story 2 — Review: approve or request changes (Priority: P2)

**Goal**: Reviewers approve or return requests in PendingReview; self-approval and
self-RequestChanges are forbidden even for dual-role users.

**Independent Test**: with a PendingReview request owned by alice (inserted via
`insert_request`), bob approves → stored Approved; carol cannot approve or return her own request
→ stored status stays PendingReview (spec US2).

### Tests for User Story 2 (write first, confirm they fail) ⚠️

- [ ] T031 [P] [US2] Write `tests/unit/domain/test_us2_review_rules.py` (no HTTP, no DB):
  `approve` by a reviewer non-owner → Approved; `request_changes` with non-blank reason →
  ChangesRequested and `changes_requested_reason` set (replacing any earlier reason, FR-011);
  requester-only or no-role caller → `Forbidden`; dual-role owner approving or requesting changes
  on own request → `Forbidden` (FR-012, FR-016); reason missing, blank or > 10,000 characters →
  `InvalidInput`; Draft/ChangesRequested/Approved → `InvalidStatus`; stale version →
  `Conflict`; self-approval with stale version → `Forbidden` (FR-020)
- [ ] T032 [P] [US2] Write `tests/api/test_us2_review.py` (HTTP + SQLite, requests created with
  `insert_request`): US2 scenarios 1–7 (200/200/403/403/422/400/403) with the stored row checked
  after each — for scenario 4 use alice approving her own PendingReview request (visible, not a
  reviewer → 403), and also check dave (cannot see it) → 404 per FR-020; reviewer views and lists all requests; role removed mid-flow — `remove_role("bob",
  "reviewer")` then bob approves → 403 and the row is unchanged, while erin can still approve
  (FR-023); dual-role carol self-approves with an outdated version → 403 (contract worked
  example); SC-001: every self-approval and self-RequestChanges attempt in this file leaves the
  stored status PendingReview

### Implementation for User Story 2

- [ ] T033 [US2] Add `approve(actor, request, body)` and `request_changes(actor, request, body)`
  to `src/changeflow/domain/rules.py`: permission = holds Reviewer **and** `actor.user_id !=
  request.requester_id` (else `Forbidden`) → `validate_version` (+ `validate_text("reason")`
  for request_changes, stored into `changes_requested_reason`) → `check_version` →
  `next_status`. Make T031 pass
- [ ] T034 [US2] Add `UseCases.approve(token, raw_id, body)` and `UseCases.request_changes(token,
  raw_id, body)` to `src/changeflow/application/use_cases.py` (authenticate → load visible →
  Domain → `_save`)
- [ ] T035 [US2] Add handlers `POST /change-requests/{id}/approve` and
  `POST /change-requests/{id}/request-changes` to `src/changeflow/api/routes.py` (same shape as
  T030, one `UseCases` call each). Make T032 and T024 pass

**Checkpoint**: all tests so far pass; US1 tests unchanged and green.

---

## Phase 5: User Story 3 — Protection against concurrent and stale changes (Priority: P2)

**Goal**: Operations based on an outdated version are rejected as `conflict`; of two operations
on the same version exactly one succeeds; nothing is partially written.

**Independent Test**: change a request once, then retry with the old version → 409 and the stored
row reflects only the first change (spec US3).

**Note**: the mechanism (Domain `check_version` + repository `update_if_version` + `_save`) was
built in Phase 2 and used by US1/US2. This story adds the deterministic SC-002 evidence. If T036
and T037 already pass, record that in the task note; T038 changes code only for failures.

### Tests for User Story 3 (write first) ⚠️

- [ ] T036 [P] [US3] Write `tests/integration/test_concurrency.py` (real SQLite, no HTTP):
  interleaving — build `UseCases` on `db_path`, load a request, change it through a second
  `UseCases` call, then call `repository.update_if_version` with the first copy's version →
  `False` and the row equals the second change; for each of edit, submit, approve and
  request-changes, two calls with the same `version` → the first succeeds and the second raises
  `Conflict`, and the stored row reflects only the first (SC-002, FR-014)
- [ ] T037 [P] [US3] Write `tests/api/test_us3_stale_writes.py` (HTTP + SQLite): US3 scenario 1
  (edit on V after V+1 → 409, row unchanged); scenario 2 (bob approves and erin requests changes,
  both with the same version → exactly one 200, the other 409, stored status matches the winner);
  scenario 3 (after a 401/403/404/400/409/422 the row's content, status and version are
  identical); all six rows of the contract "Worked examples of check order" table

### Implementation for User Story 3

- [ ] T038 [US3] Make T036 and T037 pass with changes limited to
  `src/changeflow/application/use_cases.py` (`_save` must raise `Conflict` and write nothing when
  `update_if_version` returns `False`) and `src/changeflow/infrastructure/sqlite_repository.py`
  (`update_if_version` must stay a single conditional statement); record in this task's
  checkbox note whether any change was needed

**Checkpoint**: all tests so far pass.

---

## Phase 6: User Story 4 — Correct a returned request and resubmit (Priority: P3)

**Goal**: The owner edits a ChangesRequested request and resubmits it to PendingReview; the cycle
can repeat until approval.

**Independent Test**: from a ChangesRequested request (inserted via `insert_request`), alice edits
and submits → stored PendingReview with corrected content; bob then approves (spec US4).

**Note**: the transition table (T008) already allows edit/submit from ChangesRequested, and T028
preserves `changes_requested_reason`. T041 changes code only if T039/T040 fail.

### Tests for User Story 4 (write first) ⚠️

- [ ] T039 [P] [US4] Write `tests/unit/domain/test_us4_rework_rules.py` (no HTTP, no DB): owner
  edits a ChangesRequested request → status stays ChangesRequested, version +1,
  `changes_requested_reason` kept (PA-1); owner submits it → PendingReview, reason kept;
  non-owner → `Forbidden`; full Domain cycle Draft → PendingReview → ChangesRequested →
  PendingReview → Approved using only rules functions
- [ ] T040 [P] [US4] Write `tests/api/test_us4_rework.py` (HTTP + SQLite): US4 scenarios 1–4
  (200/200; scenario 3: alice on carol's request → 404, bob on alice's request → 403;
  scenario 4: 200 then edit → 422) with stored rows checked; requester sees
  `changes_requested_reason` when viewing; end-to-end over HTTP: create → submit → request
  changes → edit → submit → approve with two users, plus SC-005 (create, submit, approve = three
  operations from new to Approved)

### Implementation for User Story 4

- [ ] T041 [US4] Make T039 and T040 pass with changes limited to `src/changeflow/domain/rules.py`
  (edit/submit must accept ChangesRequested via `TRANSITIONS` and must not clear
  `changes_requested_reason`); record in this task's checkbox note whether any change was needed

**Checkpoint**: all user stories work; `pytest` passes.

---

## Phase 7: Polish & Cross-Cutting Concerns

- [ ] T042 Create `specs/001-change-request-workflow/traceability.md`: a table mapping every
  FR-001…FR-023 and SC-001…SC-006 to the test file(s) and test function(s) that cover it; any
  requirement without a test is listed as a gap (SC-004; input for `/speckit-converge`)
- [ ] T043 Run every command in `specs/001-change-request-workflow/quickstart.md` (install, seed,
  start server, scenarios 1–10, reset) and record in
  `specs/001-change-request-workflow/quickstart-results.md` each exact command, its real output
  and status code, and whether it matched the expected result; mismatches are reported, not
  hidden (Principle IV)
- [ ] T044 Final: run `python --version`, `pip freeze` and `pytest -v` from the repository root
  with the virtual environment active, and record in
  `specs/001-change-request-workflow/test-results.md` the date, each exact command and its
  complete real output (pass/fail counts included). Do not summarise or edit the output; failing
  tests are recorded as failing (Principle IV, research R9)

---

## Dependencies & Execution Order

### Phase dependencies

- **Setup (Phase 1)** → **Foundational (Phase 2)** → **US1** → **US2** → **US3** → **US4** →
  **Polish**.
- User stories run **sequentially in priority order**, not in parallel: US1, US2 and US4 change the
  same files (`src/changeflow/domain/rules.py`, `src/changeflow/application/use_cases.py`,
  `src/changeflow/api/routes.py`), and two writers must never touch the same file at once.
- US2, US3 and US4 tests do not depend on US1 *endpoints* for their setup data (they use
  `insert_request`), so each story stays independently testable; they do depend on the US1 code
  existing in the shared files.

### Within Phase 2

- T004, T005, T006, T007 in parallel → T008 → T009 → T010 → T011 → T012 → T013 → T014 ∥ T015 →
  T016 ∥ T017 → T018 → T019 ∥ T020 ∥ T021 → T022 → T023 → T024.

### Within each story

- Test tasks [P] (different test files) first → Domain (`rules.py`) → Application
  (`use_cases.py`) → API (`routes.py`). The three implementation tasks are sequential.

### Polish

- T042 and T043 after all stories; **T044 is always the last task**.

---

## Parallel Examples

```bash
# Phase 2 start (four different files):
Task: "T004 tests/unit/domain/test_model.py"
Task: "T005 tests/unit/domain/test_rules_common.py"
Task: "T006 src/changeflow/domain/errors.py"
Task: "T007 src/changeflow/application/errors.py"

# Phase 2 infrastructure (after T013):
Task: "T014 tests/integration/test_sqlite_repository.py"
Task: "T015 tests/integration/test_sqlite_users.py"
# then
Task: "T016 src/changeflow/infrastructure/sqlite_repository.py"
Task: "T017 src/changeflow/infrastructure/sqlite_users.py"

# User Story 1 tests:
Task: "T025 tests/unit/domain/test_us1_requester_rules.py"
Task: "T026 tests/api/test_us1_create_view_list.py"
Task: "T027 tests/api/test_us1_edit_submit.py"

# User Story 2 tests:  T031 ∥ T032     User Story 3 tests:  T036 ∥ T037
# User Story 4 tests:  T039 ∥ T040
```

---

## Implementation Strategy

### MVP first (User Story 1)

1. Phase 1 Setup → Phase 2 Foundational (schema, fixtures, architecture test).
2. Phase 3 US1 → **stop and validate** with the US1 checkpoint command.

### Incremental delivery

1. Add US2 (review, no self-review) → validate.
2. Add US3 (stale-write evidence) → validate.
3. Add US4 (rework loop) → validate.
4. Polish: traceability, quickstart run, final recorded test run (T044).

Per the constitution workflow, run `/speckit-analyze` on spec, plan and tasks before starting
implementation, and resolve or accept its findings in writing.

---

## Notes

- [P] = different file from every other task in the same phase, with no dependency on an
  unfinished task.
- Verify each story's tests fail before implementing (US3/US4 are verification stories; see their
  notes).
- Commit after each task or logical group.
- Only real, reproducible results are reported (T043, T044).
