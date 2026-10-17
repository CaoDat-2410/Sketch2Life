# BE2-14 C2 PostgreSQL pack — prepared, runtime NOT_RUN

Source checkpoint: C2 commit containing this document (parent 611968d). Compare
working source with this commit and runner's before/after hashes; do not borrow
BE2-12 SQL proof. New ai_policy branch is separate from its learning_content branch.

## Preconditions and mutation scope

Only a specifically authorized disposable synthetic PostgreSQL17 environment.
No production/shared database. Restricted runner needs CREATEDB and permissions
in its own created DBs, not superuser. Configure host/port/user/maintenance DB and
existing private password file through process environment. No password arguments.
Runner does NOT download/start a service or choose/provision an environment.
Owner approval of P5 is not the separate isolated-server setup approval.

Fixture creates random ap49_<uuid> DB per case, migrates only ai_policy@head,
performs state/immutability/rollback/race/restart checks and drops only that exact
generated DB in finally. One downgrade test operates only on its disposable DB.
No provider/queue/GPU/network service is started. Child-process test receives
DB credentials only through private inherited environment, never log/CLI values.

## Executor command once the approved profile exists

From repo root, existing virtualenv, process variables supplied by trusted setup:

```powershell
# AP_TEST_PG_HOST, AP_TEST_PG_PORT, AP_TEST_PG_USER,
# AP_TEST_PG_MAINTENANCE_DB and AP_TEST_PG_PASSWORD_FILE identify the approved
# disposable environment. Never paste a password or production URL here.
$env:AP_TEST_ALLOW_CREATE = '1'
./backend/.venv/Scripts/python.exe features/FEAT-049-be2-ai-policy/src/run_c2_sql_checks.py
if ($LASTEXITCODE -ne 0) { throw 'BE2-14 PostgreSQL evidence incomplete or failed' }
```

Expected: exact 15 full JUnit test identities, no fail/error/skip/extra/duplicate,
unchanged 325 current transitive source/config/test/runner hashes, runner exit 0.
Missing explicit AP opt-in -> exit 2/NOT_RUN, even if LC opt-in exists. Missing or
skipped case -> NOT_RUN; a test error/nonzero outcome -> FAIL. No fabricated SQL
PASS from static schema checks or SQLite. Read root error before rerun.

Return ignored .runtime/ai-policy-c2/<timestamp>/summary.json, junit.xml and safe
pytest/collection logs. Do not return passwords/.env/connection strings. Setup
controller must stop/clean its approved private cluster separately; this runner
only cleans test DBs. No production migration, new server or install inferred.

## Inventory

- Module-only upgrade/downgrade/re-upgrade.
- Separate child-process restart of committed bytes and scoped outbox.
- Atomic lifecycle/receipt/event/outbox rollback.
- Concurrent global record CAS one winner.
- Duplicate receipt conflict rolls back candidate lifecycle/event.
- Six direct SQL immutability cases: body/hash/review/event/receipt/version delete.
- Review replacement order roundtrip and immutable all-proof history.
- Negative-review resubmission retains old proof but not effective approval.
- Old-version recall with new draft head does not replace that head.
- Repository rejects immutable-body rewrite with transaction rollback.

Actual owner rights/policy activation/current-source fencing and providers are
outside C2 SQL proof. They remain explicit separate integration gates.
