# FEAT-081 — Plan Revision 51A: diagnose the Parent registration database preflight

**Status:** APPROVED by the owner's 2026-11-21 instruction to inspect and fix the backend, not only the frontend. This is a narrow execution supplement to approved Plan Revision 51.  
**Product authority:** FEAT-063 canonical working SRS v2.7-draft through Rev71; unsigned. No product requirement changes.  
**Feature/worktree:** FEAT-081, task-local Compose stack `s2l-feat081-rev23`.

## Finding

During the real signup attempt, the task-local API returned 503. Its required task-local PostgreSQL container `s2l-feat081-rev23-postgres-1` was stopped with exit code 255 (not OOM-killed), while the API container continued to report healthy. The API's `get_db` dependency probes PostgreSQL before the registration route runs and returns `DATABASE_UNAVAILABLE` on failure, but currently emits no diagnostic log. The single synthetic Firebase identity from that attempt is absent. This makes a database preflight failure the likely cause; historical logs do not prove whether Firebase provisioning was reached.

The existing PostgreSQL container was started without deleting or recreating it. Its existing volume is `s2l-feat081-rev20_sketch2life-postgres`; preserve it. The task database currently contains 14 BE1 adult identity rows, zero with the seed issuer and zero with a `seed-` subject prefix.

## Scope addition

1. Add a sanitized structured log in `backend/src/sketch2life/interfaces/http/be1_runtime.py` when the request-scoped DB probe fails: request ID, exception type/module and safe SQLSTATE only. No URL, credentials, SQL, identity, or provider details.
2. Add focused coverage for the DB-unavailable diagnostic/503 behavior without starting or deleting a database.
3. Run the approved task-local API against its existing PostgreSQL container/volume, confirm `pg_isready`, DB connectivity and API health. Do not drop/recreate the volume, run seeds, or apply migrations unless a separately reviewed missing-schema finding and its exact migration are recorded first.
4. No other runtime container or data is changed.

## Acceptance

- DB unavailability returns the existing safe 503 envelope and now logs enough typed correlation data to identify the failure without exposing secrets.
- The existing task-local PostgreSQL database is reachable by the API, and its data/volume remain intact.
- All limits in Plan Revision 51 and TASK_APPROVAL Addendum 81 remain in force.

## Authorized paths

- `backend/src/sketch2life/interfaces/http/be1_runtime.py`
- focused backend contract/unit tests for `get_db`
- FEAT-081 plan, approval, status/context, and evidence paths as already authorized by Addendum 81
