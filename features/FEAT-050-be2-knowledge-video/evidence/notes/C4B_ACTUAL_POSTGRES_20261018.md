# E09 — actual isolated PostgreSQL11 PASS

2026-10-18 Asia/Saigon; parent c7b17ac, feature/be2-08-14. Owner directly replied
"duyệt" to separate08 PostgreSQL environment request. Recorded own approval/plan
before setup. No12/14 provisioning authority reused; no full-card acceptance.

## Setup / isolation

No postgres/initdb/pg_ctl/psql/Docker in PATH; existing backend Python reused.
Official [EDB binary listing](https://www.enterprisedb.com/download-postgresql-binaries)
checked still lists17.11. Downloaded portable archive from
https://get.enterprisedb.com/postgresql/postgresql-17.11-5-windows-x64-binaries.zip.
SHA25680379b2c04d51c30225532e0ae04509899141e9957ed096fe749d7fd9df8f82f
matches recorded bytes; not independent publisher signature verification.

Unique ignored .runtime/kv08-local-pg/kv08-cb174131b1a54a54995aaf526f268513;
current-user ACL, random private secret files, SCRAM, ephemeral loopback port.
Bootstrap only own cluster; generated dedicated kv08_* DB owned by runner with
(superuser,createdb,createrole)=(False,False,False). Actual server address127.0.0.1
and version17.11 verified. No service/global PATH/package/provider/GPU changes.

Local orchestration outside tracked repository (no actual secrets in source):
run_be208_pg.ps1 SHA256
699af55865ef6a5cf0266cccaaeffb7be55214b28ba3c7e53a80a3a170129aaf;
run_be208_pg_checks.py SHA256
7f1330f3f313787d12aa6eddb2316a7a7b202aed67cadcb03208d03831b6b258.
Passwords read from private files, URL only in child environment, not argv/logs.

## Result

- Existing Python `-m pytest -o addopts=` on
  tests/integration/knowledge_video/test_run_rows_sql.py with explicit private
  KV08 opt-in/loopback DB, not component runner collection-only mode.
- Exact11 node IDs match reviewed TEST_INVENTORY.json; strict JUnit identities
  PASS,11 tests,0 failures/errors/skips,1.867s, exit0. First actual run passed;
  no source fix, suppressed cases or failed SQL run to reclassify.
- Actual migration table scope, commit/reconnect/receipt persistence, rollback,
  duplicate receipt/semantic/job conflicts, scope isolation, stale/concurrent CAS,
  immutable final artifact and no terminal resurrection. Fixture refuses existing
  owned schema and downgrades only own tables/schema without CASCADE.
- 702-file source closure unchanged=True before/after; map in summary. Local
  orchestration and mutable reports are outside that map, not silently included.
- Private directory above retains collection.log/pytest.log/junit.xml/summary.json
  and initdb/start/stop/server logs. junit.xml SHA256
  2d60839c41368283422c5fc98f830111b9ac55134e3186e31d7804c444545abe;
  summary.json SHA25641240b99ff0f107567885ee47fa729cd2339ced1df975557165371434b72d62c.

## Cleanup / boundary

pg_ctl fast/wait stopped exact cluster; stop logs retained. Verified no postgres
process or remaining data/, binaries/, postgres.zip, *.secret in own runtime.
All deletion targets resolved/validated strictly beneath unique own directory,
never workspace/runtime root. Synthetic DB/binary/archive/secrets removed cannot
be restored from logs; environment can be recreated. No user/production data lost.

Own SQL gate now PASS. No actual authorized foundation run+job bridge, BE1/07/14
current authority, private staging journal, actual copy lifecycle, selected decoder
or generation proof. Reconnect is not process/cluster restart evidence. CR08-01
remains open, whole08 IN_PROGRESS.

Post-cleanup local runner PASS/exit0:459 own +1435 regression=1894, no skips,
source unchanged; Ruff/Mypy19/architecture/harness/security/diff PASS. Receipt
`.runtime/knowledge-video-component/20261018-072400-443798/summary.json`, SHA256
858ff22b1f43358242498a304995b2f1379335ee78adf096948eb1cab122aa5d.
Its SQL NOT_RUN field describes that collection-only pack, not this separate
actual SQL receipt. Security3378 publishable files checked, no sensitive findings.
