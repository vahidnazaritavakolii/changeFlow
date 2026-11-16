# Research: Change Request Workflow (First Version)

**Feature**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Date**: 2026-11-17

Each decision lists the options considered, their trade-offs, the choice and the reason.
Given by the user (not re-litigated here): Python, FastAPI, pytest.

---

## R1. Persistence

**Options**

| Option | Pros | Cons |
|--------|------|------|
| SQLite (stdlib `sqlite3`) | Zero extra service; file-based, so tests can use a fresh temp file and read the persisted state directly; supports atomic conditional `UPDATE`; no new dependency | Single writer at a time (database-level write lock); not suited to many app instances sharing one database |
| PostgreSQL | Production-grade concurrency (row locks, MVCC); multiple app instances | Needs a running server for development and tests; driver dependency; more setup than this version needs (no performance target, SC-006 removed) |
| In-memory (Python dicts) | Simplest code; fastest tests | Data lost on restart, so it is not a real system; "verify persisted state" (Principle IV) becomes meaningless; atomic check-and-set must be hand-built with locks and would not carry over to a real database |

**Decision**: SQLite through the standard-library `sqlite3` module, with plain SQL and no ORM.

**Reason**: It is the simplest option that really persists data and offers an atomic conditional
update (R2). Tests read the database file directly to verify stored state. An ORM (e.g.
SQLAlchemy) would be a new dependency and layer with no present need: there is one table of
business data and a handful of queries (Principle V).

**Operational notes**: one connection per repository call; `PRAGMA foreign_keys = ON`;
`busy_timeout` of 5 seconds so concurrent writers wait for the lock instead of failing at once.
The schema is created by an idempotent `CREATE TABLE IF NOT EXISTS` script at startup; there is
no migration tool yet, because there is only one schema version.

**What changes to migrate to PostgreSQL later**

1. Replace the two SQLite adapter modules (repository and user directory) with PostgreSQL
   versions implementing the same ports; Domain, Application and API do not change.
2. SQL dialect: `?` placeholders → `%s` (driver-dependent); `INTEGER PRIMARY KEY AUTOINCREMENT`
   → `GENERATED ALWAYS AS IDENTITY`; `CHECK` constraints carry over unchanged.
3. Add a database driver dependency and connection pooling; read the connection string from
   configuration instead of a file path.
4. Introduce a migration tool once more than one schema version exists, and a one-off data copy
   from the SQLite file.
5. Test setup: start a disposable PostgreSQL instance instead of creating a temp file.

The concurrency strategy (R2) works unchanged on PostgreSQL.

---

## R2. Concurrency control (FR-014, FR-022, SC-002)

**Options**

| Option | Pros | Cons |
|--------|------|------|
| Optimistic locking: integer `version` column, atomic conditional update `UPDATE … SET …, version = version + 1 WHERE id = ? AND version = ?` | Matches the spec directly (the caller states the version it based the change on); no locks held between requests; one statement is atomic in SQLite and PostgreSQL; deterministic to test | The losing caller must re-read and retry (this is the required behaviour) |
| Pessimistic locking (lock the row/database while checking and writing: `BEGIN IMMEDIATE` in SQLite, `SELECT … FOR UPDATE` in PostgreSQL) | Serialises writers inside one operation | Does **not** detect a caller acting on an outdated copy read in an earlier request, which the spec requires, so a version would still be needed; holds locks longer; SQLite has no row locks, so the whole database is locked |

**Decision**: optimistic locking with a `version` column and an atomic conditional update.

**How it works**

1. The caller sends `version` (the version it read) with every state-changing operation.
2. The use case loads the current request and the Domain compares `version` with the stored
   version: different → `conflict` (FR-020 step 5), before the status check (step 6).
3. If all checks pass, the repository runs the conditional update with the loaded version. If
   another writer changed the row in between, zero rows match and the result is `conflict`;
   nothing is written. So every check made on the loaded copy still holds at write time.
4. Of several operations based on the same version, at most one can match the `WHERE` clause.

**Deterministic tests for SC-002**: (a) for each state-changing operation, apply one change and
then a second with the old version → `conflict`, stored row unchanged; (b) repository-level
interleaving test: load a request, change it through a second path, then attempt the conditional
update with the first copy's version → zero rows, `conflict`. No timing-dependent stress test.

**Version transport**: a `version` field in the JSON body (not an `If-Match` header with ETags).
With a header, a missing value conventionally maps to 428 and a mismatch to 412, which would
split the spec's single "conflict" and "invalid input" categories; the body field keeps one
mapping per category (R6).

---

## R3. Authentication and authorization (FR-013, FR-015, FR-019, FR-023; spec A7)

**Options**

| Option | Pros | Cons |
|--------|------|------|
| Trusted header (`X-User-Id`) | Trivial | Verifies nothing: any caller can claim any identity. Fails Principle II |
| Self-contained signed tokens (JWT) carrying roles | Standard; no lookup for identity | Roles inside the token go stale until it expires, contradicting "current permission" (FR-013, FR-023) unless roles are looked up anyway; needs secret management, expiry and a token-issuing endpoint; new dependency |
| External identity provider (OAuth2/OIDC) | Real company single sign-on | Requires an identity provider; user administration is out of scope; heavy for this version |
| Opaque per-user API tokens (bearer), stored only as SHA-256 hashes; roles read from the database on every operation | Real identity verification (the caller must hold a secret); roles are always current; stdlib only (`secrets`, `hashlib`) | No login, expiry or rotation flow; tokens are provisioned out of band |

**Decision**: opaque bearer tokens (`Authorization: Bearer <token>`), stored hashed in a `users`
table, with roles in a `user_roles` table that is read on every operation.

**Reason**: the simplest mechanism that still verifies identity and *current* roles on every
operation. Authentication runs inside each use case as step 1 of FR-020, so the order of checks
is enforced in one place and handlers stay free of decisions.

**Simplifications in this version (stated explicitly)**

- Users, roles and tokens are provisioned with a development seed command, not an API (user and
  role administration is out of scope).
- Tokens do not expire and cannot be rotated or revoked except by editing the database.
- There is no login endpoint and no password handling.
- Transport security (HTTPS) is assumed to be provided in front of the service.
- Role checks read the roles at the start of each operation. If a role is removed in the
  milliseconds between that read and the write, the operation completes. This window is
  accepted for this version.
- This mechanism stands in for the "existing identity mechanism" of spec assumption A7, which
  stays an open reviewable assumption. Replacing it means replacing the user-directory adapter.

---

## R4. Guaranteeing that approved content cannot change (FR-009, FR-017)

**Options**

| Option | Pros | Cons |
|--------|------|------|
| Workflow-state locking: the Domain allows edits only in Draft and ChangesRequested, and defines no transition out of Approved; combined with the conditional update (R2) | No extra data; the rule lives in the Domain, so every entry point inherits it (Principle II); the version check closes the race where an edit based on a pre-approval version arrives after approval | Does not protect against someone editing the database directly |
| Content hash stored at approval | Detects later tampering | Detects but does not prevent; needs hash storage and a verification step; no requirement asks for tamper detection |
| Immutable snapshot of approved content (separate table) | Approved content kept even if the main row changes | Duplicates data; adds a table and a write path; protects against a threat the spec does not raise |

**Decision**: workflow-state locking in the Domain plus the version-conditional update.

**Reason**: it *prevents* the change through every application path, which is what the spec
requires, with no extra data or tables. Hashes and snapshots address direct database tampering
or audit needs, which are out of scope (audit history is listed as out of scope). A database
trigger rejecting updates to Approved rows was also considered as defence-in-depth and rejected
for now: no present need, and it adds dialect-specific SQL to migrate (R1).

**Tests**: Domain unit tests (edit/submit/approve/request-changes on Approved → invalid status);
HTTP tests that try to edit an Approved request and then read the database row to confirm it is
unchanged; the race test from R2 (edit with pre-approval version after approval → conflict).

---

## R5. Where input validation happens (FR-004, FR-020)

**Problem**: FR-020 requires identity, visibility and permission to be checked **before** input
validity. FastAPI normally validates request bodies with Pydantic before the handler runs, which
would report invalid input (as 422) even to unauthenticated callers.

**Options**

| Option | Pros | Cons |
|--------|------|------|
| Pydantic request models in handlers (FastAPI default) | Idiomatic; automatic schema | Validation runs first, violating FR-020; field rules (non-blank, A6 limits) would live in the API layer, violating Principle I |
| Handlers pass the raw JSON body (a dict, or a marker for "not a JSON object") to the use case; field validation is a Domain rule applied at step 4 | FR-020 order holds; validation rules live in the Domain and are unit-testable | Request schemas are not auto-generated from Pydantic; the contract is documented in `contracts/` instead |

**Decision**: raw JSON body passed to the use case; validation in the Domain at step 4. Response
bodies still use Pydantic models (output only). The path id is passed as a string so a
non-numeric id is reported as "not found" after authentication, not as a framework error.

---

## R6. HTTP mapping of outcome categories (FR-018)

**Decision**: one status code per outcome category, plus a stable machine-readable `code`:

| Outcome (spec) | HTTP | `code` |
|----------------|------|--------|
| unauthenticated | 401 (with `WWW-Authenticate: Bearer`) | `unauthenticated` |
| not found | 404 | `not_found` |
| forbidden | 403 | `forbidden` |
| invalid input | 400 | `invalid_input` |
| conflict (outdated version) | 409 | `conflict` |
| invalid status | 422 | `invalid_status` |

**Reason**: every category is distinguishable by status code alone. 409 is the standard code for
a version conflict. 400 means the request itself is invalid regardless of server state; 422 means
the request is well formed but cannot be processed in the request's current status.
**Alternative rejected**: 409 for both conflict and invalid status, distinguished only by `code`.
This is valid but makes the status code ambiguous for clients and tests.

---

## R7. Automated architecture check

**Options**

| Option | Pros | Cons |
|--------|------|------|
| `import-linter` (third-party) | Declarative import contracts | New dependency; checks imports only, not "no business conditions in handlers" |
| A pytest module using the standard-library `ast` | No dependency; checks both imports and handler bodies; runs with the normal test suite | Heuristic; must be kept in step with the folder layout |

**Decision**: `tests/architecture/test_architecture.py` using `ast`. It fails if:

1. any module in `changeflow.domain` imports `fastapi`, `starlette`, `pydantic`, `sqlite3`,
   `sqlalchemy`, `httpx`, `uvicorn`, or `changeflow.application` / `.infrastructure` / `.api`;
2. any module in `changeflow.application` imports `fastapi`, `starlette`, `sqlite3`,
   `sqlalchemy`, `uvicorn`, or `changeflow.infrastructure` / `.api`;
3. any route handler in `changeflow.api.routes` contains a branching construct (`if`,
   conditional expression, `match`, `while`, boolean operator, comparison), refers to `Status`,
   `Role`, `requester_id` or `roles`, or calls more or fewer than exactly one use case.

**Known limit**: it is a static check of the stated rules, not a proof; code review still applies.

---

## R8. Layers and abstractions kept (Principle V)

| Element | Present need |
|---------|--------------|
| Domain package | Principle I: workflow, self-review rule, validation and check order must be pure and unit-testable without HTTP or a database |
| Application package (use cases) | Principle I: handlers call exactly one use case; something must run authenticate → load → Domain → save without business conditions in handlers |
| Two ports (`ChangeRequestRepository`, `UserDirectory`) as `typing.Protocol` | Constitution: persistence depends on Application, never the reverse. Without ports the use cases would import SQLite code |
| SQLite adapters (infrastructure) | Persistence (R1) and identity lookup (R3) |
| API package | HTTP parsing, one use-case call, outcome → status mapping (R6) |

**Rejected**: ORM, dependency-injection container, generic repository/unit-of-work, service
classes per entity, DTO mapping layer, in-memory fake adapters for application tests (use cases
are covered by HTTP tests against a real temp SQLite file, which also verifies persisted state).

---

## R9. Tooling and dependencies

**Decision**: Python 3.12; `pyproject.toml` with a `src/` layout; runtime dependencies `fastapi`
and `uvicorn`; dev dependencies `pytest` and `httpx` (needed by FastAPI's `TestClient`). Minimum
versions are set in `pyproject.toml`; the exact installed versions are recorded from
`pip freeze` when tests are first run, so results are reproducible. No linters or formatters are
added in this version (no present need).
