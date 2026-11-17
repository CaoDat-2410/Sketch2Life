# E02 — actual isolated BE2-11 PostgreSQL 17 PASS

2026-10-19 Asia/Saigon; baseline2d5d925 on feature/be2-08-14. Separate actual owner
reply "duyêjt" approves the proposed combined42 SQL tests (10:14,11:17,13:11),
scoped fixes/cleanup/report/commit. Approval and LOCAL_POSTGRES_PLAN recorded in
this feature BEFORE setup. Main revision1 plan unchanged; no inherited DDL authority.

## Exact environment and command

No local PostgreSQL binaries/ready own DB found. Used existing backend Python/
psycopg/SQLAlchemy, no dependency/global installation. Official
[EDB binary listing](https://www.enterprisedb.com/download-postgresql-binaries)
verified17.11; downloaded fixed portable postgresql-17.11-5-windows-x64-binaries.zip
from get.enterprisedb.com. Archive SHA256
80379b2c04d51c30225532e0ae04509899141e9957ed096fe749d7fd9df8f82f
matches reviewed previous archive receipt; not an independent publisher signature.

Executed features/FEAT-054-be2-preset-automation/src/run_local_pg.ps1 from repo root.
It invokes run_local_pg_checks.py using existing backend/.venv/Scripts/python.exe.
Unique ignored runtime .runtime/be2-101113-pg/pg-dd5b6596ebef4ad0968286cf65bad802.
Fresh SCRAM cluster, current-user-only ACL,127.0.0.1 ephemeral port. Exact actual
PG17.11/data_directory/address/port verified before CREATE ROLE/DB. Three newly
created prefixed disposable DBs, each owned by separate NOSUPERUSER/NOCREATEDB/
NOCREATEROLE/NOREPLICATION login; actual native roles verified. No shared/prod URL,
service/PATH/provider/Lightning/GPU or teammate wiring. Private generated secrets
only file/process memory/child environment, no URL/password command arguments.

Own opt-in matched card only, previous *_TEST_DATABASE_URL/*_TEST_ALLOW_SCHEMA_DDL
stripped. Existing interpreter -m pytest -o addopts= on this card own SQL suite,
-q --tb=short --junitxml=<own-runtime>/be2-11-junit.xml; collect first and compare
reviewed exact source TEST_INVENTORY.json, then classify exact native JUnit IDs.

## Actual result

17/17 PASS, process exit0,0 failed/error/skipped/missing/extra/duplicate cases.
JUnit 3.509s (test elapsed, NOT workload/production capacity benchmark).
Node SHA256142aa09c3095b99eb4915f98aa29d0650aa2e345ebca3c67886c384c259b6305.
JUnit SHA2564fde32230cf17f0515ae27b167895d95461890e5903815e29967fa3097dd00a7.
Combined42 actual own SQL PASS, separate per-card result, no case substituted.
First actual run passed all three; no failed SQL case, application/migration/test
fix, removed assertion, waived gate, changed SQL inventory or suppressed failure.

837-file transitive source closure including PG orchestration/three environment
approvals/plans re-enumerated unchanged before/after. Combined sql-summary.json
SHA256f1ac2a86d68bba41d06b76ed452d1125a35eab342b1594057d405cec9b40610d.
Retained own collection/pytest/JUnit and shared source summary/environment/cleanup
receipts under unique ignored runtime. PS helper SHA256
020f1b511a14929c2cce2b82aed14984a945fe4dc94f4141badf2752451fdfef;
Python helper SHA2568a45620dc6b06b5db2e9fbc622e07d74303a470ea3242d480cabe19aadcef7b0.

## Cleanup / post-check / remaining boundary

pg_ctl fast/wait stopped ONLY exact own cluster. Validated resolved child paths
under unique run, removed data/, pgsql/, postgres.zip, bootstrap.secret and private
server log only. Preserved sanitized test/summary logs. Verified0 own processes,
0 listeners on the former port, no own data/binary/archive/secret/private server log.
Disposable synthetic DBs/secrets/binaries removed, not recoverable from receipts
but reproducible; no user/shared data deleted. No global service/PATH changes.

Post-cleanup consolidated component runner PASS:194 own13 +2849 prior regressions
=3043, no errors/failures/skips;830 source closure unchanged, Ruff/Mypy11 and
architecture/harness/security/diff PASS. Receipt preset-automation-component/
20261019-135427-319233 summary SHA256
67aa41d85af6182a5127801bccde0d6275bbfb1205be47adb36882d5b7f0e1da.
That intentionally SQL-disabled local runner still says SQL COLLECTED_NOT_RUN;
THIS separate E02 actual receipt supersedes earlier unexecuted SQL gate, not its
historical local-run facts. All current app/test source unchanged in actual run.

Own SQL gate now PASS. Current policy/source/BE1/P4/provider-specific adoption,
native cross-owner effect/receipt/current fencing/restart and combined acceptance
remain OPEN/NOT_RUN. Own PostgreSQL reconnect/transactions/CAS/triggers are not
actual process/cluster restart, physical intervention or production integration
proof. Full card IN_PROGRESS_PENDING_EXTERNAL, not DONE; no push/merge/deploy.
