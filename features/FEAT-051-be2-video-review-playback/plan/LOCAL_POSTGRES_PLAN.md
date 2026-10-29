# BE2-09 own PostgreSQL21 verification plan

- Status: APPROVED
- Date:2026-10-18; parent1ce8d07, branch feature/be2-08-14.
- Authority: separate direct owner "duyệt", recorded before setup.
- Main revision1 plan bytes/hash unchanged; this extends environment authorization,
  not actual BE1/source/access integration or production stack selection.

1. Use existing backend interpreter/dependencies. Download portable PostgreSQL17
   archive from official EDB source into unique ignored own runtime directory;
   record version/hash, restrict current-user ACL. No installer/service/global PATH.
2. Initialize a NEW isolated cluster, generated private secrets/SCRAM authentication,
   ephemeral loopback127.0.0.1 port only. Bootstrap only own cluster and create new
   vr09_* disposable database/limited nonsuperuser owner. Never inherited core URL.
3. Verify actual PG17/address/database/role. Re-enumerate source hashes and exact
   SQL node IDs against reviewed21-node TEST_INVENTORY.json before execution.
4. Run existing tests/integration/video_review/test_owned_sql.py with explicit09
   opt-in/private child environment; strict actual JUnit identity/outcome check,
   no skips/missing/duplicates/nonzero counted PASS. Freeze source before/after.
5. If SQL reveals defects, inspect/fix scoped code/test assumption (never suppress
   cases), document failed receipt and rerun21 +local regression with fresh pins
   when legitimately needed. Distinguish PG tests from actual bridge/access proof.
6. Stop exact own cluster, validate resolved cleanup targets beneath unique own
   runtime directory, remove cluster/binaries/archive/private secret files only.
   Preserve sanitized logs/collection/JUnit/source summary. Verify no own process/
   port/secrets remain; no broad recursive deletion/runtime-root deletion.
7. Update evidence/status/context/audit/handoff together; run local pack and security
   before checkpoint commit. No push/merge/provider/Lightning/full-card DONE claim.

Acceptance: exact21 actual SQL cases PASS with0 fail/error/skip, unchanged source,
isolated role/DB, successful exact cleanup and reproducible sanitized receipts.
Own schema transactions/CAS/triggers/reconnect evidence only; CR09-01/02 remains OPEN.
