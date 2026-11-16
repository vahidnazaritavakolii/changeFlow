# Quickstart Results: Change Request Workflow (First Version)

**Feature**: [spec.md](./spec.md) | **Guide**: [quickstart.md](./quickstart.md) | **Task**: T043
**Run date**: 2026-11-17 | **Environment**: Linux, Python 3.12.3, repository root, `.venv` active

Every command in quickstart.md was run in order. The raw output below is copied unedited from the
run's captured log.

## How the run differed from the guide (recorded, not hidden)

- **Output shortened for the install and test commands**: `pip install` and the four `pytest`
  commands were run with `2>&1 | tail -1` appended, so only their final line is recorded here.
  The complete output of the full suite is recorded by T044 in
  [test-results.md](./test-results.md).
- **The install ran over an existing `.venv`** (created in Phase 1), so `python3 -m venv .venv`
  did not create a fresh environment.
- **The server was started in the background** in the same shell, rather than in a second
  terminal as the guide describes; it was stopped after scenario 10. Its log is included below.
- **Token values are not recorded.** The `eval` of the seed command sets `ALICE_TOKEN`,
  `BOB_TOKEN` and `CAROL_TOKEN`; the log only confirms that they were set.
- Each recorded command is followed by `[exit N]`, the shell exit status, added by the run
  script. Commands without `-w '\n%{http_code}\n'` print no status code, exactly as in the guide.

## Result summary

| Step | Expected (quickstart.md) | Actual | Match |
|------|--------------------------|--------|-------|
| Install | installs | `Successfully installed changeflow-0.1.0` | Yes |
| `pytest` | all pass | 217 passed, 1 warning | Yes |
| `pytest tests/unit` | all pass, no HTTP/DB | 110 passed | Yes |
| `pytest tests/integration tests/api` | all pass | 99 passed, 1 warning | Yes |
| `pytest tests/architecture` | all pass | 8 passed | Yes |
| Seed | tokens set | 3 token variables set | Yes |
| 1 Create (Alice) | 201, Draft, version 1 | 201, Draft, version 1 | Yes |
| 2 Submit v1 | 200, PendingReview, version 2 | 200, PendingReview, version 2 | Yes |
| 3 Repeat submit, old version | 409 conflict | 409 `conflict` | Yes |
| 4 Approve without Reviewer role | 403 forbidden | 403 `forbidden` | Yes |
| 5 Request changes (Bob) | 200, ChangesRequested, version 3 | 200, ChangesRequested, version 3 | Yes |
| 6 Correct and resubmit | 200 then 200, PendingReview, version 5 | 200 (v4) then 200, PendingReview, version 5 | Yes |
| 7 Self-approval (Carol) | last call 403 forbidden | 403 `forbidden` | Yes |
| 8 Approve, then edit | 200 Approved; then 422 invalid_status | 200 Approved v6; 422 `invalid_status` | Yes |
| 9 Visibility | Alice: request 1; Bob: 1 and 2; no token: 401 | Alice: [1]; Bob: [1, 2]; 401 `unauthenticated` | Yes |
| 10 Persisted state | request 1 Approved, version 6, corrected description | `(1, 'Approved', 6, 'CSV export with id, title, status')` | Yes |
| Reset | database removed | removed (checked afterwards: no `changeflow.db`, nothing listening on port 8000) | Yes |

**Mismatches: none.** The only warning seen is the known `StarletteDeprecationWarning` from the
test client (`httpx` → `httpx2`), which does not affect results.

## Raw output

```text
### Install
$ python3 -m venv .venv
[exit 0]

$ . .venv/bin/activate
[exit 0]

$ pip install -e ".[dev]" 2>&1 | tail -1
Successfully installed changeflow-0.1.0
[exit 0]

### Test
$ pytest 2>&1 | tail -1
======================== 217 passed, 1 warning in 4.50s ========================
[exit 0]

$ pytest tests/unit 2>&1 | tail -1
============================= 110 passed in 0.08s ==============================
[exit 0]

$ pytest tests/integration tests/api 2>&1 | tail -1
======================== 99 passed, 1 warning in 4.30s =========================
[exit 0]

$ pytest tests/architecture 2>&1 | tail -1
============================== 8 passed in 0.02s ===============================
[exit 0]

### Run
$ eval "$(python -m changeflow.infrastructure.seed --db changeflow.db alice=requester bob=reviewer carol=requester,reviewer)"
[exit 0]

(token variables set: ALICE_TOKEN=<set> BOB_TOKEN=<set> CAROL_TOKEN=<set>; values not recorded)

$ CHANGEFLOW_DB=changeflow.db uvicorn --factory changeflow.api.app:create_app --port 8000   (started in background)

### Scenarios
## 1 Create (Alice)
$ curl -s -w '\n%{http_code}\n' -X POST localhost:8000/change-requests -H "Authorization: Bearer $ALICE_TOKEN" -H 'Content-Type: application/json' -d '{"title":"Add export","description":"CSV export","reason":"Audit"}'
{"id":1,"title":"Add export","description":"CSV export","reason":"Audit","requester_id":"alice","status":"Draft","version":1,"changes_requested_reason":null}
201
[exit 0]

## 2 Submit v1
$ curl -s -w '\n%{http_code}\n' -X POST localhost:8000/change-requests/1/submit -H "Authorization: Bearer $ALICE_TOKEN" -H 'Content-Type: application/json' -d '{"version":1}'
{"id":1,"title":"Add export","description":"CSV export","reason":"Audit","requester_id":"alice","status":"PendingReview","version":2,"changes_requested_reason":null}
200
[exit 0]

## 3 Repeat submit with old version
$ curl -s -w '\n%{http_code}\n' -X POST localhost:8000/change-requests/1/submit -H "Authorization: Bearer $ALICE_TOKEN" -H 'Content-Type: application/json' -d '{"version":1}'
{"error":{"code":"conflict","message":"The change request was modified by someone else; reload it and retry."}}
409
[exit 0]

## 4 Approve without Reviewer role (Alice)
$ curl -s -w '\n%{http_code}\n' -X POST localhost:8000/change-requests/1/approve -H "Authorization: Bearer $ALICE_TOKEN" -H 'Content-Type: application/json' -d '{"version":2}'
{"error":{"code":"forbidden","message":"The Reviewer role is required."}}
403
[exit 0]

## 5 Request changes (Bob)
$ curl -s -w '\n%{http_code}\n' -X POST localhost:8000/change-requests/1/request-changes -H "Authorization: Bearer $BOB_TOKEN" -H 'Content-Type: application/json' -d '{"version":2,"reason":"Add field list"}'
{"id":1,"title":"Add export","description":"CSV export","reason":"Audit","requester_id":"alice","status":"ChangesRequested","version":3,"changes_requested_reason":"Add field list"}
200
[exit 0]

## 6 Correct and resubmit (Alice)
$ curl -s -w '\n%{http_code}\n' -X PUT localhost:8000/change-requests/1 -H "Authorization: Bearer $ALICE_TOKEN" -H 'Content-Type: application/json' -d '{"title":"Add export","description":"CSV export with id, title, status","reason":"Audit","version":3}'
{"id":1,"title":"Add export","description":"CSV export with id, title, status","reason":"Audit","requester_id":"alice","status":"ChangesRequested","version":4,"changes_requested_reason":"Add field list"}
200
[exit 0]

$ curl -s -w '\n%{http_code}\n' -X POST localhost:8000/change-requests/1/submit -H "Authorization: Bearer $ALICE_TOKEN" -H 'Content-Type: application/json' -d '{"version":4}'
{"id":1,"title":"Add export","description":"CSV export with id, title, status","reason":"Audit","requester_id":"alice","status":"PendingReview","version":5,"changes_requested_reason":"Add field list"}
200
[exit 0]

## 7 Self-approval (Carol)
$ curl -s -X POST localhost:8000/change-requests -H "Authorization: Bearer $CAROL_TOKEN" -H 'Content-Type: application/json' -d '{"title":"Fix retry","description":"Retry 3x","reason":"Flaky jobs"}'
{"id":2,"title":"Fix retry","description":"Retry 3x","reason":"Flaky jobs","requester_id":"carol","status":"Draft","version":1,"changes_requested_reason":null}[exit 0]

$ curl -s -X POST localhost:8000/change-requests/2/submit -H "Authorization: Bearer $CAROL_TOKEN" -H 'Content-Type: application/json' -d '{"version":1}'
{"id":2,"title":"Fix retry","description":"Retry 3x","reason":"Flaky jobs","requester_id":"carol","status":"PendingReview","version":2,"changes_requested_reason":null}[exit 0]

$ curl -s -w '\n%{http_code}\n' -X POST localhost:8000/change-requests/2/approve -H "Authorization: Bearer $CAROL_TOKEN" -H 'Content-Type: application/json' -d '{"version":2}'
{"error":{"code":"forbidden","message":"You cannot review your own change request."}}
403
[exit 0]

## 8 Approve (Bob), then edit after approval (Alice)
$ curl -s -w '\n%{http_code}\n' -X POST localhost:8000/change-requests/1/approve -H "Authorization: Bearer $BOB_TOKEN" -H 'Content-Type: application/json' -d '{"version":5}'
{"id":1,"title":"Add export","description":"CSV export with id, title, status","reason":"Audit","requester_id":"alice","status":"Approved","version":6,"changes_requested_reason":"Add field list"}
200
[exit 0]

$ curl -s -w '\n%{http_code}\n' -X PUT localhost:8000/change-requests/1 -H "Authorization: Bearer $ALICE_TOKEN" -H 'Content-Type: application/json' -d '{"title":"x","description":"x","reason":"x","version":6}'
{"error":{"code":"invalid_status","message":"'edit' is not allowed when the request is Approved."}}
422
[exit 0]

## 9 Visibility
$ curl -s localhost:8000/change-requests -H "Authorization: Bearer $ALICE_TOKEN"
{"items":[{"id":1,"title":"Add export","description":"CSV export with id, title, status","reason":"Audit","requester_id":"alice","status":"Approved","version":6,"changes_requested_reason":"Add field list"}]}[exit 0]

$ curl -s localhost:8000/change-requests -H "Authorization: Bearer $BOB_TOKEN"
{"items":[{"id":1,"title":"Add export","description":"CSV export with id, title, status","reason":"Audit","requester_id":"alice","status":"Approved","version":6,"changes_requested_reason":"Add field list"},{"id":2,"title":"Fix retry","description":"Retry 3x","reason":"Flaky jobs","requester_id":"carol","status":"PendingReview","version":2,"changes_requested_reason":null}]}[exit 0]

$ curl -s -w '\n%{http_code}\n' localhost:8000/change-requests
{"error":{"code":"unauthenticated","message":"Authentication required."}}
401
[exit 0]

## 10 Persisted state
$ python3 -c "import sqlite3; print(sqlite3.connect('changeflow.db').execute('select id,status,version,description from change_requests').fetchall())"
[(1, 'Approved', 6, 'CSV export with id, title, status'), (2, 'PendingReview', 2, 'Retry 3x')]
[exit 0]

(server stopped)

### Reset
$ rm -f changeflow.db
[exit 0]
```

## Server log (uvicorn)

```text
INFO:     Started server process [75951]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     127.0.0.1:43060 - "GET /docs HTTP/1.1" 200 OK
INFO:     127.0.0.1:43070 - "POST /change-requests HTTP/1.1" 201 Created
INFO:     127.0.0.1:43076 - "POST /change-requests/1/submit HTTP/1.1" 200 OK
INFO:     127.0.0.1:43080 - "POST /change-requests/1/submit HTTP/1.1" 409 Conflict
INFO:     127.0.0.1:43092 - "POST /change-requests/1/approve HTTP/1.1" 403 Forbidden
INFO:     127.0.0.1:43108 - "POST /change-requests/1/request-changes HTTP/1.1" 200 OK
INFO:     127.0.0.1:43112 - "PUT /change-requests/1 HTTP/1.1" 200 OK
INFO:     127.0.0.1:43114 - "POST /change-requests/1/submit HTTP/1.1" 200 OK
INFO:     127.0.0.1:43116 - "POST /change-requests HTTP/1.1" 201 Created
INFO:     127.0.0.1:43120 - "POST /change-requests/2/submit HTTP/1.1" 200 OK
INFO:     127.0.0.1:43130 - "POST /change-requests/2/approve HTTP/1.1" 403 Forbidden
INFO:     127.0.0.1:43146 - "POST /change-requests/1/approve HTTP/1.1" 200 OK
INFO:     127.0.0.1:43154 - "PUT /change-requests/1 HTTP/1.1" 422 Unprocessable Entity
INFO:     127.0.0.1:43158 - "GET /change-requests HTTP/1.1" 200 OK
INFO:     127.0.0.1:43162 - "GET /change-requests HTTP/1.1" 200 OK
INFO:     127.0.0.1:43168 - "GET /change-requests HTTP/1.1" 401 Unauthorized
INFO:     Shutting down
INFO:     Waiting for application shutdown.
INFO:     Application shutdown complete.
INFO:     Finished server process [75951]
```
