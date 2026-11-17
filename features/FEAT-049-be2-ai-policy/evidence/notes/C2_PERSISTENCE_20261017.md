# C2 — lifecycle persistence code / offline checks, PG runtime NOT_RUN

2026-10-17 Asia/Saigon. Branch feature/be2-08-14, parent 611968d. Approved
revision 1/P5; plan bytes unchanged. Preimplementation matrix C2_PERSISTENCE.md.
Executor self-review, not independent owner review or runtime verification.

## Code

Own ai_policy schema, six tables: scoped record/head/global revision, immutable
version body/hash/author/time, append-only exact review/history, scoped command
receipt, safe lifecycle metadata event, scoped outbox FK. SQL UoW commits all
changes together; UPDATE parent fence for writes, SHARE parent fence for reads.
Exact version missing does not fallback. Review replacement reconstructs latest
dimension in review-revision order, old contexts/proofs remain in bounded history.
Write guards reject body hash/immutable rewrite, stale CAS, inherited approvals
on fresh version and mutations of superseded unpublished versions. No authority
or adopted registry/policy decisions inferred by the repository.

Frozen independent migration 20261017_ap_0001 has no mutable metadata imports;
DDL matches compiled metadata. Triggers protect immutable version fields,
terminal/publication metadata and review/receipt/event history. Additive Alembic
metadata/schema allowlist preserves core/ai_jobs/learning_content. No previously
published migration changed. Trigger syntax/behavior is still unproven on actual
PostgreSQL until runtime pack executes; text/offline render is not that proof.

C3 effective scope/kill epoch/reservation tables not invented ahead of usage;
will be forward migration with actual application behavior. No provider/model/
production value selection, auth bypass, default-route mounting or owner-table writes.

## Actual local checks

Existing backend .venv, cwd backend:

```powershell
.venv/Scripts/python.exe -m pytest -o addopts= tests/contract/test_ai_policy_contracts.py tests/unit/test_ai_policy_domain.py tests/unit/test_ai_policy_persistence_shape.py tests/unit/test_ai_policy_sql_runner.py -q --tb=short
.venv/Scripts/python.exe -m mypy --follow-imports=silent src/sketch2life/infrastructure/ai_policy src/sketch2life/application/ports/ai_policy.py
```

Final JUnit .runtime/be2-14-c2/component-final-junit.xml: 160 PASS, no fail/error/
skip, 1.44s. 78 contracts +46 domain +26 offline/guard/schema/Alembic +10 runner
classification. 36 new C2 cases, not 160 newly implemented cases. Focused Ruff
over changed source/tests/migration/env/runner PASS; strict Mypy four C2 source
files PASS with imported dependency checking suppressed for focused scope.
Earlier lint import/line length/nested-context findings corrected; no test or
security gate weakened. Existing Alembic path_separator warnings retained.

Existing FEAT048 component command at repo root:
.runtime/learning-content-component/20261017-134506-149512 summary/JUnit/logs:
477 selected cases PASS, no skip, 3.97s, source unchanged. Its defined lint/type/
architecture/harness/security/diff all exit 0. Two separate inventories sum to
637 local PASS; this is not BE2-14 SQL proof. Earlier regression receipt before
final review-order/env changes is superseded by this last source-pinned run.

## Runtime prepared, not executed

15 real PG17 test cases collected successfully (0.30s). Runner pins 325 current
transitive source/config/test/runner files and verifies exact full JUnit identity,
no missing/duplicate/extra/skip/failure, before/after source unchanged. Ten unit
classifier cases prove evidence handling only. AP_TEST_ALLOW_CREATE and approved
profile required; LC opt-in does not authorize BE2-14 DB mutations.
Actual no-profile runner invocation printed NOT_RUN and exited 2; no SQL test,
server start, download, credential creation or install occurred. Missing runtime
cannot be counted PASS. Separate isolated PG17 setup/test/cleanup approval has
been requested from owner; no reply interpreted as permission.

Reproduction/preconditions/impact/expected inventory/log return:
artifacts/C2_SQL_RUNTIME.md. Includes 15 checks for module migration, restart,
rollback, record CAS, receipt uniqueness, direct immutable SQL, replacement/
resubmit history, old-version recall/new head and immutable payload rejection.
Fixture synthetic actors are not real authority/fence integration proof.

Source SHA256:

- infrastructure/ai_policy/sql.py:
  fed56452463235f39c5e7b09644ae525b0f6b385bedb8a4b8d799c6189d74a01
- alembic/versions/20261017_ap_0001_policy_lifecycle.py:
  81f84e9b3c4c7929018eb0a82abed1dc2581811bb178ec6097e3134bbd8d765a
- FEAT049 src/run_c2_sql_checks.py:
  d800ac8fb079073ebdb1ceb86324d80d0d0a46dc62e25168db3833249b62dad1

## Remaining

C2 actual SQL proof pending environment approval. C3 activation/registry/budget/
kill, C4 provider-copy trusted verification, C5 real command handler/projections,
C6 consolidated review/handoff still required. Existing BE2-12 33 SQL evidence
is historical for that source; additive Alembic env changed and does not gain
fresh actual SQL PASS from 477 component regressions. Owner integration deferred
to teammates, not waived. No BE2-14 runtime/production-ready/full-card DONE claim.
