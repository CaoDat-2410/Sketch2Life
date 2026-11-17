# E07 — actual isolated PostgreSQL21 PASS

2026-10-18 Asia/Saigon, parent1ce8d07, feature/be2-08-14. Separate direct owner
"duyệt" approves temporary local PostgreSQL17/21 own SQL cases/scoped fixes/cleanup/
report/checkpoint. Recorded approvals/LOCAL_POSTGRES_APPROVAL.md and
plan/LOCAL_POSTGRES_PLAN.md before setup. Main reviewed revision1 bytes unchanged,
SHA256eca121bb1ce17943936bb68cbbbce62777f6a3867c5ef4cf70594ba9838d82e7.

## Environment / isolation

No ready09 DB/opt-in/PostgreSQL tools/service available in inspected environment.
Used existing backend interpreter/psycopg/SQLAlchemy, no dependency installation.
Official [EDB binary listing](https://www.enterprisedb.com/download-postgresql-binaries)
verified lists17.11. Downloaded portable archive from
https://get.enterprisedb.com/postgresql/postgresql-17.11-5-windows-x64-binaries.zip.
SHA25680379b2c04d51c30225532e0ae04509899141e9957ed096fe749d7fd9df8f82f
matches prior recorded archive bytes; not independent publisher signature proof.

Unique ignored runtime .runtime/vr09-local-pg/vr09-52233351e70245808fab37be12e701ed,
current-user-only inherited ACL. Portable bin/lib/share only, no installer/global
PATH/service. Fresh cluster, generated private secret files/SCRAM, ephemeral port
bound127.0.0.1 only. Bootstrap limited to own cluster; generated vr09_* database
owned by separate test role (superuser,createdb,createrole)=(False,False,False).
Actual server address/version17.11/role checked before tests, not URL assertion alone.

Local orchestration outside tracked repo, no literal secrets/URL in argv/reports:
run_be209_pg.ps1 SHA256
8082534046027116d5ea9d6a58ab7273ba20deb14d2d460fd4a411f1ced84224;
run_be209_pg_checks.py SHA256
361482f63780dece7f18ad27a994c0a8d35a93050ec7753dc5895eb14b9f0e92.
Passwords read from private generated files; DB URL only in child environment.
No inherited core/shared/prod DB, provider/GPU/Lightning or08 opt-in reuse.

## Actual measured result

- Existing interpreter -m pytest -o addopts= on
  tests/integration/video_review/test_owned_sql.py, explicit own09 private opt-in,
  not the collection-only component pack.
- Reviewed exact21 collection nodes match TEST_INVENTORY.json cases21/node SHA256
  31953969d0579b779922cf6df17777673ac30e699be975eb639f33b517c128a2.
- Actual21 PASS,0 failure/error/skip,4.338s JUnit (pytest reports4.35s), process exit0.
  Strict JUnit testcase identity classifier PASS, not just count/exit code. First
  actual run passed; no failed SQL run, suppressed case, test/source fix or pin edit.
- Verified frozen migration six own tables, scoped receipt/head persistence,
  rollback of all writes, initial/lifecycle CAS race one winner, review/change
  shared key conflict, original history/archive, all append-only tables update/
  delete refusal, head revision/changed-subject copied approval trigger refusal,
  playback pending/receipt terminal persistence, unique key/whole transaction abort,
  pending intent/history/event rollback and connection reopen after pool disposal.
  Connection reopen is not actual process/cluster restart or cross-owner proof.
-733-file source closure re-enumerated before/after unchanged=True: local runner's
  full backend/transitive feature runner/config sources plus separate own SQL
  approval/environment plan. Source map in retained summary; orchestration scripts
  hashed separately, not silently counted as tracked source inventory.
- Ignored retained logs collection.log/pytest.log, JUnit and summary in own runtime
  above, alongside initdb/start/stop/server logs. junit.xml SHA256
  0fc6b2205ff598f2ede0f9fab341a4ec19420b7b5f1a89b3260d9087cf4c7073;
  summary.json SHA256e857976c03fcaf6e0767b2ebfcb83ddc1ef0542664f680a766b102fe7dd6ab97.

## Cleanup / post-check / remaining gates

pg_ctl fast/wait stopped exact own cluster. Removed only resolved/validated data/,
binaries/, postgres.zip and two *.secret targets strictly beneath unique own run
directory, never runtime/workspace root. Verified no own data/binary/archive/secret
file and0 postgres/pg_ctl/initdb processes remain. Disposable synthetic DB/binaries/
secrets cannot be restored from retained logs; can be recreated. No user data lost.

Post-cleanup local one-batch PASS,458 own +1894 regression=2352, no skips; source
unchanged and Ruff/Mypy17/architecture/harness/security/diff PASS. Receipt
.runtime/video-review-component/20261018-085755-058596/summary.json SHA256
b71d0e58487543571544346c20ea9f30a65f9fe488ef5112daa5315dbdd85359.
Its SQL COLLECTED_NOT_RUN describes that deliberately SQL-disabled pack, NOT this
separate actual SQL receipt. Final grouped report security/harness/diff checked
again before checkpoint commit; no runtime secrets/artifacts staged.

Own09 SQL gate now PASS; internal09 complete. Actual canonical head/source/policy/
consent adoption CR09-01, actual BE1 session/access/receipt/fetch/range/resume and
revocation adoption CR09-02, selected08 decoder/generation/quality/owner acceptance
remain OPEN/NOT_RUN. Own SQL21 PASS does not turn full09 into DONE or prove those
external gates. No push/merge/deploy/global service/provider/Lightning activation.
