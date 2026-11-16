# Quickstart: Change Request Workflow (First Version)

**Feature**: [spec.md](./spec.md) | **Contract**: [contracts/http-api.md](./contracts/http-api.md)

> Status: these are the **planned** commands. They become runnable once the tasks are
> implemented. Results must be reported only from real runs (Constitution Principle IV).

## Prerequisites

- Linux or macOS with Python 3.12+ and `curl`.
- Run all commands from the repository root.

## Install

```bash
python3 -m venv .venv
```

```bash
. .venv/bin/activate
```

```bash
pip install -e ".[dev]"
```

## Test

Full suite (domain unit tests, HTTP tests against a temporary SQLite file, architecture check):

```bash
pytest
```

By group:

```bash
pytest tests/unit
```

```bash
pytest tests/integration tests/api
```

```bash
pytest tests/architecture
```

Expected: all tests pass; `tests/unit` needs neither HTTP nor a database.

## Run

Create demo users and print their tokens as shell variables (development only, research R3):

```bash
eval "$(python -m changeflow.infrastructure.seed --db changeflow.db alice=requester bob=reviewer carol=requester,reviewer)"
```

Start the API:

```bash
CHANGEFLOW_DB=changeflow.db uvicorn --factory changeflow.api.app:create_app --port 8000
```

## End-to-end validation scenarios

Run in a second terminal after the `eval` line above (the variables `ALICE_TOKEN`, `BOB_TOKEN`,
`CAROL_TOKEN` must be set there too). Expected status codes follow the contract.

1. **Create** (Alice, Requester) → `201`, `status` `Draft`, `version` 1:

   ```bash
   curl -s -w '\n%{http_code}\n' -X POST localhost:8000/change-requests -H "Authorization: Bearer $ALICE_TOKEN" -H 'Content-Type: application/json' -d '{"title":"Add export","description":"CSV export","reason":"Audit"}'
   ```

2. **Submit** with version 1 → `200`, `status` `PendingReview`, `version` 2:

   ```bash
   curl -s -w '\n%{http_code}\n' -X POST localhost:8000/change-requests/1/submit -H "Authorization: Bearer $ALICE_TOKEN" -H 'Content-Type: application/json' -d '{"version":1}'
   ```

3. **Repeat submit with the old version** → `409 conflict`:

   ```bash
   curl -s -w '\n%{http_code}\n' -X POST localhost:8000/change-requests/1/submit -H "Authorization: Bearer $ALICE_TOKEN" -H 'Content-Type: application/json' -d '{"version":1}'
   ```

4. **Approve without the Reviewer role** (Alice) → `403 forbidden`:

   ```bash
   curl -s -w '\n%{http_code}\n' -X POST localhost:8000/change-requests/1/approve -H "Authorization: Bearer $ALICE_TOKEN" -H 'Content-Type: application/json' -d '{"version":2}'
   ```

5. **Request changes** (Bob, Reviewer) → `200`, `status` `ChangesRequested`, `version` 3:

   ```bash
   curl -s -w '\n%{http_code}\n' -X POST localhost:8000/change-requests/1/request-changes -H "Authorization: Bearer $BOB_TOKEN" -H 'Content-Type: application/json' -d '{"version":2,"reason":"Add field list"}'
   ```

6. **Correct and resubmit** (Alice) → `200` then `200`, `status` `PendingReview`, `version` 5:

   ```bash
   curl -s -w '\n%{http_code}\n' -X PUT localhost:8000/change-requests/1 -H "Authorization: Bearer $ALICE_TOKEN" -H 'Content-Type: application/json' -d '{"title":"Add export","description":"CSV export with id, title, status","reason":"Audit","version":3}'
   ```

   ```bash
   curl -s -w '\n%{http_code}\n' -X POST localhost:8000/change-requests/1/submit -H "Authorization: Bearer $ALICE_TOKEN" -H 'Content-Type: application/json' -d '{"version":4}'
   ```

7. **Self-approval** (Carol holds both roles; she creates and submits her own request, id 2,
   then tries to approve it) → last call `403 forbidden`:

   ```bash
   curl -s -X POST localhost:8000/change-requests -H "Authorization: Bearer $CAROL_TOKEN" -H 'Content-Type: application/json' -d '{"title":"Fix retry","description":"Retry 3x","reason":"Flaky jobs"}'
   ```

   ```bash
   curl -s -X POST localhost:8000/change-requests/2/submit -H "Authorization: Bearer $CAROL_TOKEN" -H 'Content-Type: application/json' -d '{"version":1}'
   ```

   ```bash
   curl -s -w '\n%{http_code}\n' -X POST localhost:8000/change-requests/2/approve -H "Authorization: Bearer $CAROL_TOKEN" -H 'Content-Type: application/json' -d '{"version":2}'
   ```

8. **Approve** request 1 (Bob) → `200`, `status` `Approved`; then **edit after approval**
   (Alice) → `422 invalid_status`:

   ```bash
   curl -s -w '\n%{http_code}\n' -X POST localhost:8000/change-requests/1/approve -H "Authorization: Bearer $BOB_TOKEN" -H 'Content-Type: application/json' -d '{"version":5}'
   ```

   ```bash
   curl -s -w '\n%{http_code}\n' -X PUT localhost:8000/change-requests/1 -H "Authorization: Bearer $ALICE_TOKEN" -H 'Content-Type: application/json' -d '{"title":"x","description":"x","reason":"x","version":6}'
   ```

9. **Visibility**: Alice lists → only request 1; Bob lists → requests 1 and 2; no token → `401`:

   ```bash
   curl -s localhost:8000/change-requests -H "Authorization: Bearer $ALICE_TOKEN"
   ```

   ```bash
   curl -s localhost:8000/change-requests -H "Authorization: Bearer $BOB_TOKEN"
   ```

   ```bash
   curl -s -w '\n%{http_code}\n' localhost:8000/change-requests
   ```

10. **Persisted state check** — request 1 is Approved at version 6 with the corrected
    description:

    ```bash
    python3 -c "import sqlite3; print(sqlite3.connect('changeflow.db').execute('select id,status,version,description from change_requests').fetchall())"
    ```

## Reset

```bash
rm -f changeflow.db
```
