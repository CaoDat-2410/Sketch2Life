# C6d — actual local PostgreSQL104 PASS, not full-card acceptance

2026-10-18 Asia/Saigon, feature/be2-08-14 parent0e192da. Owner directly replied
"duyệt" after explicit isolated local PostgreSQL17 synthetic test/cleanup request.
Recorded separate approval before provisioning; no prior BE2-12 authority reused.
Read AGENTS/current context/source register/current SQL pack and fixture, existing
BE2-12 environment lessons. Scoped C6d execution plan before setup. No inherited
approval to touch cloud/shared/production DB or actual BE1/P4/provider/GPU stack.

## Environment / isolation

Official EDB portable17.11 Windows x64 archive from
https://get.enterprisedb.com/postgresql/postgresql-17.11-5-windows-x64-binaries.zip,
listed version verified via https://www.enterprisedb.com/download-postgresql-binaries.
SHA25680379b2c04d51c30225532e0ae04509899141e9957ed096fe749d7fd9df8f82f
matched prior recorded bytes, not independent publisher signature verification.
Existing project Python3.12 environment reused, no pip/GPU/Docker install,
Windows service/global PATH or default application mount. Helper generated in
local artifact workspace, not production package or credentials committed to Git.

Unique ignored .runtime/ap-local-pg/ap-<uuid>, current-user-only ACL, random secret
files, SCRAM, loopback IPv4 ephemeral port. Bootstrap role only provisions this
new cluster. Probe host(inet_server_addr()) exactly127.0.0.1, server_version17.11,
runner flags(superuser=False,createdb=True,createrole=False). Tests create/drop only
generated ap49_<uuid> databases with restricted role. Synthetic external guards/
hooks retain labels; SQL success is not real owner fencing/provider proof.

## Failures retained / actual correction

1. First prep ap-c703a52608ee46a99954681a94b6b597 started/stopped cluster but
   inet::text address assertion failed due representation; changed probe to
   host(inet_server_addr()). No tests claimed for failed preparation. Cleanup
   removed cluster/binaries/archive/secrets, preserving start/stop/server logs.
2. Second runtime ap-700e7bda8638401383e5da75c6a5990e:15 lifecycle PASS receipt
  20261017-183813-186775,10 activation PASS183828-600133,21 accounting PASS
  183843-348625. Copy58 suite receipt20261017-183907-582568 had56 PASS/2 FAIL.
   Root errors: purge/cancel report test unpacked3 values from resolution_service,
   whose contract returns2(service,envelope). Actual SQL setup/migrations ran,
   but those2 report assertions were not reached; no false PASS assigned.
3. Correct only tests/integration/ai_policy/test_copy_registry_sql.py report call
   from service,_,op to service,op. Existing helper/other callers/source confirmed.
   No application/domain/migration/shared foundation change or test suppression.
4. Third runtime ap-83f94a4ff6e54009a26c647447c5b9b4 reruns ALL four packs on
   corrected source. Failures remain in prior receipts, not overwritten/relabelled.
   Ruff initially launched once from root showed import-classification mismatch;
   rerun in documented backend cwd PASS, no import/source rewriting. A read-only
   report formatting command had a PowerShell pipe parse error, corrected without
   affecting controller/test processes.

## Final actual SQL results

Runner: existing Python features/FEAT-049-be2-ai-policy/src/run_c2_sql_checks.py,
then --activation, --accounting, --copies, explicit AP_TEST_* approved profile.
Private secret values passed only by environment/file, not argv/logs.

| Pack | Cases | JUnit seconds | Ignored receipt under .runtime/ai-policy-c2/ |
|---|---:|---:|---|
| lifecycle |15 PASS|12.251|20261017-184056-815585|
| activation/stop/use |10 PASS|9.670|20261017-184112-568336|
| ledger/operations |21 PASS|40.304|20261017-184125-328005|
| inventory/operation/receipt/report |58 PASS|43.158|20261017-184208-755128|

Total104 PASS, zero failure/error/skip, exact inventories/no duplicate/extra cases,
all runner exit0 and source_unchanged=true. Each receipt collection.log/junit.xml/
pytest.log/summary.json pins backend/transitive tests/migrations/config/runner.
Existing Alembic path_separator deprecations recorded (17/10/21/60 warnings per
pack), no warning suppression. Original lifecycle tests pin ap_0001; later packs
upgrade ai_policy@head throughap_0009. Scope atomicity/race/history/proof/CAS/
rollback/reconnect tests now executed, not merely collected/offline metadata.
Do not overstate separate-process restart beyond the explicit lifecycle child-
process case; other reconnect tests recreate engine/adapter as their source states.

## Cleanup / handoff

All three own clusters stopped with pg_ctl fast/wait and startup/shutdown logs
retained. Verified each runtime has no data/, binaries/, postgres.zip, *.secret;
no remaining postgres process observed. Recursive deletion targets resolved
absolute paths and checked strictly beneath each unique run directory, never
workspace/runtime root. Temporary generated DBs/data/binary/ZIP/secrets removed
and not recoverable except by recreating synthetic environment. Logs/receipts
retained in ignored runtime; no child data/model/media used or deleted.

Final exact local1061 own/114 foundation/477 selected regression and64 source
lint/typecheck/security pack rerun after evidence/docs before commit. Timestamped
receipt printed by runner/final chat; no code edits during source-pinned run.
Own SQL gate now PASS, while actual authority/registry/telemetry/provider adapters,
generation-safe kill contract/delivery and full BE1/P4 conformance remain open.
No whole-card/original BE2-12 goal DONE, other task activation, push/merge/deploy.
