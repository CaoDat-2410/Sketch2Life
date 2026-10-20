# BE2-13 receiver handoff / local versus actual verification

Branch feature/be2-08-14; approval direct "duyệt", revision1 P1–P4;
frozen plan601afab84123ee5dd48aa04cf643ea7cd904f53675a0b16a9c007684660e1548.
CONTRACT_HANDOFF.md and ACCEPTANCE_AUDIT.md define delivered interfaces and actual
unfinished work. No default service/router/scheduler/provider registration.

Current E02:11/11 actual own PostgreSQL PASS, combined10/11/13 SQL42 PASS; separate
approval recorded and isolated PG17.11 fully cleaned. Post-cleanup3043 local PASS.
Actual BE1/current policy/scheduler adoption still OPEN; SQL steps below reproduce
the now-executed gate. Combined environment command from repo root (Windows):
features/FEAT-054-be2-preset-automation/src/run_local_pg.ps1. It requires approved
LOCAL_POSTGRES_APPROVAL/PLAN in all three features and provisions NEW own DBs only.

## One local command

```powershell
backend/.venv/Scripts/python.exe features/FEAT-054-be2-preset-automation/src/run_component_checks.py
```

Run at repo root with existing interpreter, Linux equivalent backend/.venv/bin/python.
Exact owned/regression/SQL node inventory is src/TEST_INVENTORY.json. Runner strips
ALL *_TEST_DATABASE_URL and *_TEST_ALLOW_SCHEMA_DDL child opt-ins, only COLLECTS own
SQL. It does not install/provision/download or invoke actual BE1/provider/Lightning.
Prior regression includes01/12/14/08–11/foundation plus legacy catalog fixture suites;
legacy ranker uses injected fake transport, not an actual model call.

Ignored .runtime/preset-automation-component/UTC-run contains collection/process
logs, exact JUnit, before/after source hashes and summary. PASS requires exact
frozen plan/approval/node identities/JUnit with no missing/extra/duplicate/skipped/
failed/error, no nonzero exit, unchanged re-enumerated source closure and applicable
Ruff/Mypy/architecture/harness/security/diff gates. No recursive previous runner main.
Source covers transitive backend/tests/migrations/helpers, feature src/JSON and
catalog/config inputs. Mutable prose/metrics are not executable source proof.
Do not replace pins to hide failures. Legitimate new cases require source/evidence
reviewed inventory update. full_card_complete remains false for local PASS.

## Actual own PostgreSQL (separate authorization)

11 prepared tests/integration/preset_automation/test_owned_sql.py. Require newly
dedicated loopback PG17 pa13_* database name length>=12, private
PA13_TEST_DATABASE_URL (postgresql+psycopg) and PA13_TEST_ALLOW_SCHEMA_DDL=1 in child
environment. Never print connection secrets or inherit other cards' DDL permission.
Fixture refuses existing schema; creates/drops exact own schema via frozen upgrade/
downgrade, no CASCADE, no global service/server/database provisioning or deletion.

Run existing interpreter in backend with -m pytest -o addopts=
tests/integration/preset_automation/test_owned_sql.py --junitxml=<ignored-runtime>/sql.xml.
Capture exact pinned11 node IDs, source closure before/after, JUnit/status/environment;
0 fail/error/skip with proper isolation required for actual own SQL PASS.
Cases: frozen tables/trigger upgrade, reconnect/history/scope, whole rollback,
competing CAS single winner, history update/delete and head delete refusal,
terminal requires exact persisted receipt, effect/terminal rollback, native receipt
immutability, foreign scope rejection. Connection reopen not actual process/cluster
restart evidence. SQL schema tests alone not actual BE1 command atomicity.

## Actual adoption / delayed combined test

Teams implement Authority/Fence held verified non-I/O snapshots/current fences,
SessionCommands.lookup/reconcile/execute with real exact receipts/atomic BE1 epoch
checks/dedup and QueuePolicy; scheduler adapter explicitly invokes evaluate/dispatch/
reconcile. BE1 owns effective session/config storage, not13 SQL. Existing12 primary
dispatcher consumes bind_preset; actual production route mounting remains separate.

Test Teacher draft source pin ->conditional queued intent ->Teacher override/disable
->old queued/in-flight action stale at BE1 effect boundary. Preserve exact source
hash, expected/effective versions, native intent hash/receipt, audit and current
state before/after. Negatives for wrong Teacher/class, current revoked consent/
source/review/safety, library edits, unadopted rule/config, stale epochs/stage,
duplicate/conflicting keys, delayed ACK/reconciliation/native restart and overload.
Never infer physical cancellation, current config or child achievement from own
queued/sending/applied history. No autoapprove/complete/purge, provider activation
or live video generation required to verify13. Real workload limits need actual
approved measurement profile/pilot and owner acceptance, not a new default number.
