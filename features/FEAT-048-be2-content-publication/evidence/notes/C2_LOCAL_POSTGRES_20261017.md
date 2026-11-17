# C2 direct local PostgreSQL result — 2026-10-17 (Asia/Saigon)

Status: C2_POSTGRES_PASS. Not whole-card completion.

## Authority and isolated environment

Owner replied "duyệt" to the explicit portable PostgreSQL 17 test setup,
autonomous test and cleanup proposal. Approval addendum is recorded in
approvals/TASK_APPROVAL.md. No inherited approval to touch production or a
teammate's Studio was used.

Downloaded PostgreSQL 17.11 Windows x64 portable binaries from official EDB:
https://www.enterprisedb.com/download-postgresql-binaries
and its listed download redirected to
https://get.enterprisedb.com/postgresql/postgresql-17.11-5-windows-x64-binaries.zip.
Archive SHA256:
80379b2c04d51c30225532e0ae04509899141e9957ed096fe749d7fd9df8f82f.
This hash records downloaded bytes, not a claim of independent publisher-signature
verification. Existing Python 3.12 project environment was reused; no pip, Docker,
GPU/model install, Windows service or global PATH change.

The cluster used a unique ignored runtime directory, current-user-only ACL,
random password files, SCRAM and loopback IPv4 only. Direct socket/role probes
confirmed 127.0.0.1 and role flags (superuser false, createdb true, createrole
false). Bootstrap superuser was used only on this newly created private cluster
to provision the restricted runner role, not to run the tests.

## Failures preserved and actual correction

1. Windows controller initially used Start-Process -Wait for pg_ctl. It waited
   for the server descendant although pg_ctl had exited and the server log
   said ready. The verified wrapper alone was stopped; the same running
   cluster was retained. Changed to Process.WaitForExit on the exact helper.
2. First actual SQL run: 1 passed / 8 failed, no skipped.
   Alembic read cached CoreDatabaseSettings containing the first already-dropped
   disposable DB URL. This was a test environment isolation bug, not a reason
   to disable cases or relax DB checks.
3. Fixed only the content integration fixture by clearing the configuration
   cache before/after each case; no global settings or BE1/foundation test code
   was changed. Same server then passed all nine cases.
4. Strengthened the restart case: dispose parent pool, invoke a separate Python
   process/new engine through a private environment DSN, assert different PID
   and recover exact committed hash/revision/event/outbox. The old same-process
   reconstruction is not claimed as independent process restart proof.

Raw initial FAIL and subsequent PASS receipts remain private under .runtime.
They were not overwritten or relabelled. Public metric includes only safe
counts, hashes, role/cleanup facts and relative artifact pointers.

## Final actual commands/results

From repository root with authorized LC_TEST_* runtime variables:

- Existing Python -> feature src/run_c2_sql_checks.py:
  **9 passed, 0 failures/errors/skips, 10.72s; runner PASS/exit 0**.
- From backend, pytest on content domain/contracts/persistence shape/C2 runner/
  content integration plus ai_job_contracts, ai_job_polling and ai_job_lifecycle:
  **211 passed, no skipped, 14.53s**.
- Eleven existing Alembic path_separator deprecation warnings are recorded,
  not hidden or counted as failures. No unrelated global config changed.
- Receipt source hashes bind the exact tested files; current metric:
  evidence/metrics/C2_LOCAL_POSTGRES_20261017.json.
- The fixed hidden process-control helper was directly exercised on the same
  cluster: graceful stop, start returned in 0.6s, then graceful stop. This
  verifies the waiting fix, not an additional full application/runtime claim.

## Cleanup

Read-only SQL found zero remaining lc_48_* disposable databases.
Server was gracefully stopped; PID file absent and test port not listening.
Logs were copied to ignored .runtime/local-pg-c2/ storage (no secret files).
An initial computed-path forced cleanup command was rejected by the command
safety layer before execution. After read-only validation of the exact UUID
directory and stopped state, native PowerShell removal of that explicit literal
temporary path without Force succeeded; existence check returned false.
Cluster, random credentials, binaries and downloaded ZIP are removed. No shared
workspace directory or unrelated files were removed. Reproduction requires
recreating the portable runtime; sanitized receipts/private logs remain.

## Limits

C2 demonstrates owned-schema migration, atomic rollback, cross-process reads,
scoped storage, CAS race behavior and immutable-history guards. It does not
prove full publication service, HTTP/auth integration, policy/source authority,
real cross-owner adoption or production readiness. C3/C4/C5 remain required.
The portable setup controller's startup helper was corrected and smoke-tested;
the successful suite was resumed on the existing cluster rather than redownloading
and repeating its entire setup workflow.
