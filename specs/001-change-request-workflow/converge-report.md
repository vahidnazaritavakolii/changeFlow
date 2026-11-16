# Converge Report: Change Request Workflow (First Version)

**Feature**: [spec.md](./spec.md) | **Tasks**: [tasks.md](./tasks.md) (Phases 8–10)
| **Test evidence**: [test-results.md](./test-results.md) | **Date**: 2026-11-17

This report records the three `/speckit-converge` rounds run after all 44 planned tasks were
done, the two convergence tasks implemented (T045, T046), why the existing tests missed each gap,
and what remains open.

**Human acceptance has not been evaluated.** No responsible person has yet evaluated the human
acceptance criteria or recorded a real result. Under the constitution ("Development Workflow &
Quality Gates"), the feature is therefore **implemented but not complete**.

Conventions:

- Each "Round output" is the converge report as originally given in the session, copied
  unchanged.
- Test outputs are the raw tool outputs, copied unchanged. The exact command is given above each.
- Each "Change" is the source diff taken from `git show` of the fix commit.

---

## Round 1 (produced T045)

### Round output

````text
Converge found one gap, so it appended one task to tasks.md as `## Phase 8: Convergence`. Nothing else in tasks.md changed, no code changed, and nothing is committed. No extension hooks are registered.

## Convergence Findings

| ID | Gap Type | Severity | Source | Evidence | Remaining Work |
|----|----------|----------|--------|----------|----------------|
| F1 | contradicts | CRITICAL | Constitution II; plan: HTTP contract | FastAPI serves its built-in pages by default. `GET /docs`, `/redoc`, `/openapi.json` and `/docs/oauth2-redirect` each returned **200 with no token** in a live probe. The contract says "Every endpoint requires `Authorization: Bearer <token>`" and that any other path returns 404 or 405. Constitution II says access is denied unless explicitly allowed. | Turn the pages off in `create_app` and add a test that they return 404 or 405 → **T045** |

**On the severity:** the rules mark any constitution violation as CRITICAL, so I did. In practice the risk is low: these pages expose only the API's shape, no change-request data, and they don't even describe request bodies. They were never planned, though, and nothing in the spec or plan allows them.

**What else I checked, with no other gaps found:**
- **Requirements:** all 23 FRs, the 6 SCs, every acceptance scenario of US1–US4 and the edge cases. Each was checked against the code and the passing tests (217 passing, re-run during this check).
- **Plan decisions:** R1–R9 (SQLite, the version-checked write, bearer tokens with roles read on every call, edit-locking by status, validation in the Domain, the status-code mapping, the architecture test, the layering, the tooling) and PA-1–PA-7.
- **Constitution:** all six principles. I confirmed:
  - only `api/app.py` imports the storage code from outside it;
  - every use case runs identity check → load and visibility check → Domain rule → version-checked save;
  - every Domain operation checks permission first.

**By gap type:** 0 missing, 0 partial, 1 contradicts, 0 unrequested. **By severity:** 1 critical.

**Next:** run `/speckit-implement` to complete T045 (Phase 8), then run converge again. It should then report converged, unless you'd rather keep the docs pages. In that case the contract and plan would need to say so explicitly, and T045 would be dropped.

These are outside converge's scope but still needed before the feature counts as "complete": a person's check of each human acceptance criterion with the real result recorded, and README.md (H3). Your answers on the Phase 4 404 behaviour and on `httpx2` are also still open.
````

### T045 — Failing test before the fix

Test added: `test_framework_documentation_endpoints_are_not_served` in
`tests/api/test_us1_create_view_list.py`.

Command: `pytest tests/api/test_us1_create_view_list.py -k framework_documentation -p no:warnings 2>&1 | tail -12`

```text
tests/api/test_us1_create_view_list.py:178: AssertionError
=========================== short test summary info ============================
FAILED tests/api/test_us1_create_view_list.py::test_framework_documentation_endpoints_are_not_served[no-token-/docs]
FAILED tests/api/test_us1_create_view_list.py::test_framework_documentation_endpoints_are_not_served[no-token-/redoc]
FAILED tests/api/test_us1_create_view_list.py::test_framework_documentation_endpoints_are_not_served[no-token-/openapi.json]
FAILED tests/api/test_us1_create_view_list.py::test_framework_documentation_endpoints_are_not_served[no-token-/docs/oauth2-redirect]
FAILED tests/api/test_us1_create_view_list.py::test_framework_documentation_endpoints_are_not_served[valid-token-/docs]
FAILED tests/api/test_us1_create_view_list.py::test_framework_documentation_endpoints_are_not_served[valid-token-/redoc]
FAILED tests/api/test_us1_create_view_list.py::test_framework_documentation_endpoints_are_not_served[valid-token-/openapi.json]
FAILED tests/api/test_us1_create_view_list.py::test_framework_documentation_endpoints_are_not_served[valid-token-/docs/oauth2-redirect]
======================= 8 failed, 23 deselected in 0.50s =======================
```

### T045 — Change (commit `8470289`)

```diff
diff --git a/src/changeflow/api/app.py b/src/changeflow/api/app.py
index 9568398..6304382 100644
--- a/src/changeflow/api/app.py
+++ b/src/changeflow/api/app.py
@@ -15,7 +15,8 @@ from changeflow.infrastructure.sqlite_users import SqliteUserDirectory
 def create_app(db_path: str | None = None) -> FastAPI:
     path = db_path or os.environ.get("CHANGEFLOW_DB", "changeflow.db")
     init_schema(path)
-    app = FastAPI(title="ChangeFlow")
+    # No unauthenticated documentation endpoints (Constitution II, HTTP contract; T045).
+    app = FastAPI(title="ChangeFlow", docs_url=None, redoc_url=None, openapi_url=None)
     app.state.use_cases = UseCases(
         SqliteChangeRequestRepository(path), SqliteUserDirectory(path)
     )
```

### T045 — Full suite after the fix

Command: `pytest`

```text
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.2.0, pluggy-1.7.0
rootdir: /home/vahid/Desktop/SoftwareEngineeringInArtificialInteligenceEra/Project-01/changeFlow
configfile: pyproject.toml
testpaths: tests
plugins: anyio-4.16.0
collected 225 items

tests/api/test_us1_create_view_list.py ...............................   [ 13%]
tests/api/test_us1_edit_submit.py ................                       [ 20%]
tests/api/test_us2_review.py .................                           [ 28%]
tests/api/test_us3_stale_writes.py .........                             [ 32%]
tests/api/test_us4_rework.py .......                                     [ 35%]
tests/architecture/test_architecture.py ........                         [ 39%]
tests/integration/test_concurrency.py ..........                         [ 43%]
tests/integration/test_sqlite_repository.py ..........                   [ 48%]
tests/integration/test_sqlite_users.py .......                           [ 51%]
tests/unit/domain/test_model.py .....                                    [ 53%]
tests/unit/domain/test_rules_common.py ................................. [ 68%]
...............                                                          [ 74%]
tests/unit/domain/test_us1_requester_rules.py .......................... [ 86%]
.                                                                        [ 86%]
tests/unit/domain/test_us2_review_rules.py .........................     [ 97%]
tests/unit/domain/test_us4_rework_rules.py .....                         [100%]

=============================== warnings summary ===============================
tests/api/test_us1_create_view_list.py::test_requester_creates_draft
  /home/vahid/Desktop/SoftwareEngineeringInArtificialInteligenceEra/Project-01/changeFlow/.venv/lib/python3.12/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================== 225 passed, 1 warning in 4.58s ========================
```

### Why the existing tests did not detect F1

- The HTTP tests were written from the contract's endpoint list, so they only exercised routes
  the contract names. The "unlisted routes" test (`test_delete_and_unlisted_routes_are_rejected`)
  tried `DELETE`, `/reject` and `/cancel`, but no test tried the paths FastAPI adds **by
  itself**.
- The architecture test (T024) inspects the handlers in `api/routes.py`. The documentation
  routes are registered by `FastAPI()` itself, not in `routes.py`, so the test never saw them.
- The evidence was available but nobody acted on it: during T043 the quickstart run script used
  `GET /docs` only to wait for the server to start, and the server log recorded
  `GET /docs HTTP/1.1" 200 OK`. Nobody checked that 200 against the contract.

### Note between Round 1 and Round 2 (a wrong verdict)

After T045, a converge re-run reported, in its own words:

````text
**✅ Converged — the implementation satisfies the spec, plan, and tasks.**
````

That verdict was wrong: the code already had the gap that Round 2 found (the code did not change
between the two runs). That run re-checked the specified behaviours but did not try unusual
inputs.

---

## Round 2 (produced T046)

### Round output

````text
This converge run found a gap my previous run missed, so the earlier "✅ Converged" verdict was wrong. A very large numeric request id makes the API crash with a 500 error instead of answering "not found". I appended one task, T046, as `## Phase 9: Convergence`. No code changed and nothing is committed. No extension hooks are registered.

The code hadn't changed since that run. The difference is that this time I tried unusual inputs as well.

## Convergence Findings

| ID | Gap Type | Severity | Source | Evidence | Remaining Work |
|----|----------|----------|--------|----------|----------------|
| F2 | partial | HIGH | Spec Edge Cases ("Request does not exist"); FR-018 | A numeric id beyond SQLite's 64-bit integer range returns **500 Internal Server Error** instead of 404 `not_found`. This affects view, edit, submit, approve and request-changes; I tried a 25-digit id and 2⁶³. Cause: `UseCases._load_visible` sends any all-digit id to `SqliteChangeRequestRepository.get`, and `sqlite3` raises `OverflowError: Python int too large to convert to SQLite INTEGER`. The largest valid value, 2⁶³−1, already correctly returns 404. | Have `get` return `None` for ids outside SQLite's range (a storage limit, so the fix stays in the storage layer) and add HTTP and repository tests → **T046** |

**Unusual inputs that behave correctly:**

| Input | Result |
|-------|--------|
| A very large `version` on an existing request | 409 `conflict` |
| Id `0` | 404 |
| JSON `null`, `NaN` or non-UTF-8 bytes as the body | 400 `invalid_input` |
| Id `0001` | Resolves to request 1. That's an integer, not covered by PA-6's "non-numeric" rule, so it isn't a gap. |

**Re-checked:**
- 23 FRs, 6 SCs, every US1–US4 acceptance scenario and the edge cases
- plan decisions R1–R9 and PA-1–PA-7
- all 6 constitution principles
- all 45 existing tasks, including T045: the docs pages still return 404

The suite still passes, 225 of 225, because no test used an id this large.

**By gap type:** 0 missing, 1 partial, 0 contradicts, 0 unrequested. **By severity:** 1 high.

**Next:** run `/speckit-implement` on T046, then converge again. Since `test-results.md` was re-recorded before this gap was found, it will need recording once more after T046. The re-recorded version is also still uncommitted.
````

### T046 — Failing tests before the fix

Tests added: `test_id_beyond_storage_range_is_not_found_for_every_operation` in
`tests/api/test_us1_create_view_list.py`; `test_get_id_outside_integer_range_returns_none` and
`test_get_at_integer_range_limits_returns_none_when_unknown` in
`tests/integration/test_sqlite_repository.py`.

Command (output filtered to result lines and the exception, then counted):
`pytest tests/api/test_us1_create_view_list.py tests/integration/test_sqlite_repository.py -k "beyond_storage_range or integer_range" -p no:warnings 2>&1 | grep -E "^(FAILED|PASSED|ERROR)|passed|failed|OverflowError: " | sort | uniq -c | sort -rn`

```text
      5 E           OverflowError: Python int too large to convert to SQLite INTEGER
      1 FAILED tests/integration/test_sqlite_repository.py::test_get_id_outside_integer_range_returns_none[-9223372036854775809]
      1 FAILED tests/integration/test_sqlite_repository.py::test_get_id_outside_integer_range_returns_none[9223372036854775808]
      1 FAILED tests/integration/test_sqlite_repository.py::test_get_id_outside_integer_range_returns_none[10000000000000000000000000]
      1 FAILED tests/api/test_us1_create_view_list.py::test_id_beyond_storage_range_is_not_found_for_every_operation[2**63]
      1 FAILED tests/api/test_us1_create_view_list.py::test_id_beyond_storage_range_is_not_found_for_every_operation[25-digits]
      1 ================== 5 failed, 1 passed, 41 deselected in 0.65s ==================
```

The one pass is the boundary test (2⁶³−1 and −2⁶³), which already worked. It guards against a fix
that is off by one.

### T046 — Change (commit `c0570ee`)

```diff
diff --git a/src/changeflow/infrastructure/sqlite_repository.py b/src/changeflow/infrastructure/sqlite_repository.py
index f008c14..dbdafdf 100644
--- a/src/changeflow/infrastructure/sqlite_repository.py
+++ b/src/changeflow/infrastructure/sqlite_repository.py
@@ -10,6 +10,10 @@ _COLUMNS = (
     "id, title, description, reason, requester_id, status, version, changes_requested_reason"
 )
 
+# SQLite INTEGER is a signed 64-bit value; sqlite3 raises OverflowError outside it.
+_SQLITE_INT_MIN = -(2**63)
+_SQLITE_INT_MAX = 2**63 - 1
+
 
 def _to_entity(row: sqlite3.Row) -> ChangeRequest:
     return ChangeRequest(
@@ -29,6 +33,8 @@ class SqliteChangeRequestRepository:
         self._db_path = db_path
 
     def get(self, id: int) -> ChangeRequest | None:
+        if not _SQLITE_INT_MIN <= id <= _SQLITE_INT_MAX:
+            return None  # no stored request can have this id (T046)
         conn = connect(self._db_path)
         try:
             row = conn.execute(
```

### T046 — Full suite after the fix

Command: `pytest`

```text
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.2.0, pluggy-1.7.0
rootdir: /home/vahid/Desktop/SoftwareEngineeringInArtificialInteligenceEra/Project-01/changeFlow
configfile: pyproject.toml
testpaths: tests
plugins: anyio-4.16.0
collected 231 items

tests/api/test_us1_create_view_list.py ................................. [ 14%]
                                                                         [ 14%]
tests/api/test_us1_edit_submit.py ................                       [ 21%]
tests/api/test_us2_review.py .................                           [ 28%]
tests/api/test_us3_stale_writes.py .........                             [ 32%]
tests/api/test_us4_rework.py .......                                     [ 35%]
tests/architecture/test_architecture.py ........                         [ 38%]
tests/integration/test_concurrency.py ..........                         [ 43%]
tests/integration/test_sqlite_repository.py ..............               [ 49%]
tests/integration/test_sqlite_users.py .......                           [ 52%]
tests/unit/domain/test_model.py .....                                    [ 54%]
tests/unit/domain/test_rules_common.py ................................. [ 68%]
...............                                                          [ 75%]
tests/unit/domain/test_us1_requester_rules.py .......................... [ 86%]
.                                                                        [ 87%]
tests/unit/domain/test_us2_review_rules.py .........................     [ 97%]
tests/unit/domain/test_us4_rework_rules.py .....                         [100%]

=============================== warnings summary ===============================
tests/api/test_us1_create_view_list.py::test_requester_creates_draft
  /home/vahid/Desktop/SoftwareEngineeringInArtificialInteligenceEra/Project-01/changeFlow/.venv/lib/python3.12/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================== 231 passed, 1 warning in 4.99s ========================
```

### Why the existing tests did not detect F2

- The "unknown id" tests used small or obviously invalid values (`999`, `abc`, `1.5`, `-1`,
  `0`). The failure only appears above 2⁶³−1, and no test went there.
- The limit belongs to SQLite, not to the spec. The spec only says "an unknown request is not
  found", so tests written from the spec had no reason to try that boundary.
- The use case accepts any all-digit string (PA-6 only defines *non-numeric* ids), and
  the Domain unit tests never reach SQLite. The only place the value could overflow, the
  repository, was tested with real ids only.

---

## Round 3 (produced T047 and T048 — not implemented)

### Round output

````text
I did both. The test results are re-recorded with 231 of 231 passing, but converge found two more inputs that crash the API, so it is not converged yet. It appended T047 and T048 as `## Phase 10: Convergence`. No code changed and nothing is committed. No extension hooks are registered.

**1. [test-results.md](specs/001-change-request-workflow/test-results.md).** I ran `python --version`, `pip freeze` and `pytest -v` at commit `c0570ee`, with `git status` empty at run time:

```text
======================== 231 passed, 1 warning in 5.05s ========================
[exit 0]
```

The file is generated from the captured output without edits. It lists the earlier runs (217, 217, 225) it replaces.

**2. Converge.** Since my earlier "converged" verdict missed a crash, this time I sent 114 deliberately unusual requests across all seven endpoints. Four came back as 500 errors, from two causes:

## Convergence Findings

| ID | Gap Type | Severity | Source | Evidence | Remaining Work |
|----|----------|----------|--------|----------|----------------|
| F3 | partial | HIGH | FR-004, FR-018 | JSON allows text escapes like `"\ud800"` (a half of a character pair, invalid on its own). `json.loads` accepts it, it passes `validate_text`, and then `sqlite3` raises `UnicodeEncodeError`. Confirmed 500 on create (title), edit of a Draft (description) and request-changes (reason). | Reject such text as `invalid_input` in `validate_text` (`rules.py`), with unit and HTTP tests → **T047** |
| F4 | partial | HIGH | FR-018, plan R5 | A body nested 100,000 levels deep makes `json.loads` raise `RecursionError`. `json_body` (`http_io.py`) catches only `ValueError` and `UnicodeDecodeError`, so the error escapes as a 500 on every endpoint that reads a body. | Also catch `RecursionError` in `json_body` and return `INVALID_BODY`, with an HTTP test → **T048** |

**Unusual inputs that behave correctly (the other 110 probes):**
- ids: `+1`, `1.0`, `0x1`, Arabic-Indic `٣`, full-width `１`, 2⁶³, a 400-digit id (the T046 fix holds)
- bodies: NUL bytes, emoji, a 5,000-digit version, `Infinity`, duplicate keys, a byte-order mark
- `Authorization` headers: non-ASCII, 100,000-character, lowercase `bearer`, tab separator

**Re-checked as before, still fine:** 23 FRs, 6 SCs, the US1–US4 acceptance scenarios, R1–R9, PA-1–PA-7, the constitution, and all 46 existing tasks.

**By gap type:** 0 missing, 2 partial, 0 contradicts, 0 unrequested. **By severity:** 2 high.

**A broader point:** these crashes, and the one fixed in T046, all came from inputs nobody listed in the spec. Each converge run with new unusual inputs can turn up more. One general safeguard would close the whole class: an exception handler that turns any *unexpected* error into a JSON 500 with no internal details. That would mean adding a sixth outcome category to the contract, so it's a spec and plan decision for you rather than a converge task.

**Next:** `/speckit-implement` on T047 and T048, then re-record the test results and converge again. The re-recorded `test-results.md` is also uncommitted.
````

T047 and T048 were **not implemented** for this deadline. There is no fix, failing-test output or
post-fix suite output for them; their analysis is under "Remaining gaps and open tasks" below.

### Why the existing tests did not detect F3 and F4

- **F3 (unpaired surrogates).** The text-validation tests covered blank, missing, too-long and
  non-string values, all built in Python. A JSON escape such as `"\ud800"` produces a value that
  *is* a `str`, is not blank and is short, so it passes every check. Only the SQLite write rejects
  it, and no test sent such an escape over HTTP.
- **F4 (deep nesting).** The body tests sent malformed text, an empty body and a JSON array, all
  of which raise `ValueError` or parse cleanly. `json_body` was written assuming parse errors
  are always `ValueError`. Python's parser instead hits its recursion limit on deep nesting, and
  no test went near it.

### Common cause across F1–F4

The tests are example-based and were derived from the spec's scenarios and the contract's
endpoint list. They prove the specified behaviour, but they cannot cover inputs or routes nobody
wrote down: framework defaults, storage limits, Unicode edge cases, parser limits. Converge
Rounds 1 and the re-run in between also checked only the specified behaviour. Only when unusual
inputs were tried (Rounds 2 and 3) did these gaps appear. The current suite (231 passing) still
contains no general fuzz or property-based tests.

---

## Remaining gaps and open tasks

### Open convergence tasks (not implemented for this deadline)

| Task | Finding | Severity | Status |
|------|---------|----------|--------|
| T047 | F3: unpaired-surrogate text → 500 | HIGH | Open; not implemented |
| T048 | F4: deeply nested JSON body → 500 | HIGH | Open; not implemented |

**T047 — analysis.**
- **Requirement:** FR-004 (input validity) and FR-018 (every rejection reports a defined
  category).
- **Behaviour today:** a title, description or reason containing an unpaired surrogate escape
  (for example `"\ud800"`) passes `validate_text`, then `sqlite3` raises `UnicodeEncodeError`.
  The request fails with 500 on create, on edit of a Draft, and on request-changes.
- **Impact:** nothing is stored, because the error happens at the write, so data integrity holds.
  But the caller gets an undefined outcome instead of `invalid_input`.
- **Planned fix:** in `validate_text` (Domain), reject values that cannot be encoded as UTF-8,
  with unit and HTTP tests.

**T048 — analysis.**
- **Requirement:** FR-018 and plan research R5 (bodies are parsed in `http_io` and invalid
  bodies become `invalid_input`).
- **Behaviour today:** a body nested about 100,000 levels deep makes `json.loads` raise
  `RecursionError`. `json_body` does not catch it, so every endpoint that reads a body answers
  500.
- **Impact:** nothing is stored. Each such request makes the server do expensive parsing before
  it fails.
- **Planned fix:** also catch `RecursionError` in `json_body` and return `INVALID_BODY`, with an
  HTTP test.

**After T047 and T048:** re-record `test-results.md` and run converge again, including
unusual-input probes.

### Wider gap: undefined errors are possible

- T046, T047 and T048 are three instances of one class: an unexpected exception reaches the
  framework and becomes a plain-text 500.
- The contract defines six outcome categories and no response for unexpected errors.
- A general handler that returns a JSON error with no internal details would close the class.
  It needs a spec and contract decision, so it is not a converge task.
- Until that decision, other unexpected inputs may still produce 500s.

### Other open items

- **Human acceptance: not evaluated.** No responsible person has evaluated the human acceptance
  criteria or recorded a real result, so the feature is not complete under the constitution.
- **Phase 4 decision awaiting confirmation:** a reviewer who loses the Reviewer role gets 404
  `not_found` (they can no longer see the request; FR-015 and FR-020), not the 403 that the T032
  task text expected. The tests assert 404.
- **Dependency warning:** `StarletteDeprecationWarning` recommends `httpx2` instead of `httpx`.
  Changing it would alter plan research R9, so it awaits a decision.
- **README.md** (analysis finding H3): accepted as "written after converge". Not written,
  because converge has not reached a clean result.

### State of the evidence at the time of this report

- **Tasks:** 46 of 48 done (T001–T046). T047 and T048 are open.
- **Latest recorded full run** ([test-results.md](./test-results.md)): commit `c0570ee`, clean
  tree, 231 passed, 0 failed, 1 warning.
- **Quickstart run** ([quickstart-results.md](./quickstart-results.md)): before T045 and T046.
  All 10 scenarios matched at that time. It has not been re-run since.
