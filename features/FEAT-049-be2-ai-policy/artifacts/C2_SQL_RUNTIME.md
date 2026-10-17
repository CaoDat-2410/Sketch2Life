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

Fixture creates random ap49_<uuid> DB per case, migrates lifecycle tests to pinned
20261017_ap_0001 and activation tests to ai_policy@head,
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
./backend/.venv/Scripts/python.exe features/FEAT-049-be2-ai-policy/src/run_c2_sql_checks.py --activation
if ($LASTEXITCODE -ne 0) { throw 'BE2-14 activation SQL evidence incomplete or failed' }
./backend/.venv/Scripts/python.exe features/FEAT-049-be2-ai-policy/src/run_c2_sql_checks.py --accounting
if ($LASTEXITCODE -ne 0) { throw 'BE2-14 ledger SQL evidence incomplete or failed' }
./backend/.venv/Scripts/python.exe features/FEAT-049-be2-ai-policy/src/run_c2_sql_checks.py --copies
if ($LASTEXITCODE -ne 0) { throw 'BE2-14 copy inventory SQL evidence incomplete or failed' }
```

Expected: exact 15 lifecycle +10 activation/stop/current-use +19 ledger +19 copy
inventory SQL JUnit test identities (63 total) in four separate
receipts, no fail/error/skip/extra/duplicate,
unchanged current transitive source/config/test/runner hashes, runner exit 0.
Missing explicit AP opt-in -> exit 2/NOT_RUN, even if LC opt-in exists. Missing or
skipped execution case -> NOT_RUN; collection mismatch or test error/nonzero
outcome -> FAIL. No fabricated SQL
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
- Activation pack: actual commands publish/disable/restart pin, receipt-failure
  rollback of lifecycle+scope intent, concurrent publications linearize to one pin,
  recall of old pin racing replacement cannot disable the new pin.
- Emergency-stop additions: before-publication stop persists and replays after
  restart; receipt failure rolls back lazy scope/epoch/intent; stale-epoch stop
  racing reviewed activation cannot disable replacement.
- Current-use additions: old exact request pin survives ordinary replacement;
  stop history and forged later epoch deny resurrection after reactivation;
  real feature SHARE lease blocks stop's update until consumer exits. Lock test
  checks actual pg_stat_activity wait_event_type, not a sleep/future alone.
- Ledger additions: ap_0003 upgrade through current head, committed reservation
  and terminal proof survive connection disposal/reconnect (not a process restart
  claim); atomic reserve rollback; duplicate receipt rolls back counters/audit;
  concurrent budget and global slot caps admit one winner; new window retains
  old occupied slots; same attempt cannot reserve again under a different window;
  exact live/terminal replay does not duplicate audit or counters; verified fixture
  release frees original bucket/slot; audit failure rolls back terminal settlement;
  fixture overrun retained and blocks new reserve; five raw-SQL immutable-history
  cases; wrong org/feature denied. All numeric values/evidence synthetic, not
  production definitions/provider cost. Two added SQL component cases compose
  actual policy/ledger transactions with guarded reserve/settle and after-stop
  reconcile (still ASSUMED external owner/quote/evidence). Real current-owner
  fencing and actual provider verification are not proven by those fixtures.

Prepared ledger cases: tests/integration/ai_policy/test_accounting_sql.py. They
remain NOT_RUN until authorized PostgreSQL execution; offline compilation, codec
tests and inventory validation do not prove transaction/race behavior.

Actual owner rights/policy activation/current-source fencing and providers are
outside C2 SQL proof. They remain explicit separate integration gates.

## Copy inventory pack (`--copies`)

Own ap_0004 original registrations/profile refs; unknown empty read without writes;
duplicate exact no-op, three provenance-conflict cases; atomic scope/register/event
rollback; reconnect (not separate process restart); revision-pinned keyset paging
and stale scan rejection; coverage report invalidation/CAS/cross-scope rejection;
registration vs purge scope race and late initial quarantine; concurrent duplicate
register; five raw-SQL immutable-original/coverage/audit/unpurge cases; read-only/
org/scope isolation; missing-scope reader cannot mix a later insert into revision0.
19 prepared actual SQL cases, NOT_RUN until authorized profile executes this pack.
Inventory/coverage code is not current-copy lifecycle, actual discovery/deletion,
provider dispatch/cancellation or BE1 overall request closure proof.
