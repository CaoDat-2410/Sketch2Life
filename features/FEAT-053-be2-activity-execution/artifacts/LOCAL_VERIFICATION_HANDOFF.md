# BE2-11 receiver handoff / reproducible local and delayed actual verification

Branch feature/be2-08-14; approved revision1 P1–P4, frozen SHA256
09348e0fcafb96370c3c58e99ae5b8a8eaee16d416694066985086ecde09ac1d.
Internal implementation complete; full acceptance pending actual SQL/source/policy/
BE1/P4 proof. HTTP_CONTRACT_HANDOFF.md and ACCEPTANCE_AUDIT.md are current entrypoints.

## Delivered surfaces

domain/activity_execution: immutable Definition/Audience/Adaptations/Assignment,
explicit preparation/ExecutionProof and action-state matrix/invalidation; source
snapshot separate from effective local changes. application/activity_execution and
ports/activity_execution: current owner guards, per-child checks, CAS/idempotent
commands/history, authenticated notice and one-event outcome delivery/ACK protocol.
application/activity_discovery: exact12 definition asset join +scoped catalog source
for BE1 CMD-59, broad topic/exact-age/preference candidate semantics, warnings not
hard readiness/material filtering. infrastructure/activity_execution/ranking maps
exact aliases to existing ranker DTO, no actual provider/default weights selected.

Own five-table schema assignment/history/receipt/event/ack, closed codec/new
20261019_ae_0001 migration, scoped PostgreSQL adapter/own advisory lock +domain
transition revalidation/CAS/history/unique receipts and immutable exact ACK. No12/
BE1/foundation SQL/FKs or published migration edits. Own locks not current authority.
Injected CMD-45 strict transport/output, no app registration/default identity,
Child mutation route or competing CMD-59/46/47. Outcome remains result-reference
handoff, not fabricated observation/reflection/portfolio or automatic session advance.

## One local command, no external effects

```powershell
backend/.venv/Scripts/python.exe features/FEAT-053-be2-activity-execution/src/run_component_checks.py
```

Run from repo root with existing interpreter (Linux backend/.venv/bin/python).
Exact inventory src/TEST_INVENTORY.json: owned, prior08–10/12/14/foundation regression,
legacy catalog/preparation/ranking tests, own SQL collection-only. Output ignored
.runtime/activity-execution-component/UTC-run has collection/process logs, exact
JUnit/source map/hashes and summary. PASS requires approved frozen plan, exact pinned
node identities/no skips/duplicates/missing/extra/nonzero, source re-enumeration
unchanged and Ruff/Mypy/architecture/harness/security/diff all0. Source includes
transitive backend Python/feature helpers/manifests +legacy data JSON/tool scripts.
Local runner strips all *_TEST_DATABASE_URL/*_TEST_ALLOW_SCHEMA_DDL opt-ins; SQL
NEVER runs. full_card_complete=false even local PASS. No package/model/HTTP provider
activation by runner; legacy ranker tests use injected transport fixtures.

Do not update pins to hide failures or call another runner main recursively. Legitimate
new tests need reviewed exact pins/evidence; mutable evidence prose not source proof.

## Actual own SQL: separate environment authorization

Prepared tests/integration/activity_execution/test_owned_sql.py17 cases. Need owner-
approved NEW dedicated disposable loopback PG17 ae11_* DB(length>=12), driver
postgresql+psycopg. AE11_TEST_DATABASE_URL private child env plus explicit
AE11_TEST_ALLOW_SCHEMA_DDL=1. Never inherit09/10/12 approval, print credentials or
use shared/production DB. Fixture refuses existing schema; own upgrade/downgrade
only, exact created objects without CASCADE, no server/database auto-provisioning.

Capture exact17 nodes/reviewed hashes and source before. Existing backend interpreter
in backend: -m pytest -o addopts= tests/integration/activity_execution/test_owned_sql.py
--junitxml=<ignored-own-runtime>/junit.xml. Match exact JUnit identities/outcomes with
same classifier as local pack and re-enumerate unchanged sources. Only0 fail/error/
skip +proper isolation means actual SQL PASS; retain/fix failures without weakening.

Cases: frozen five tables, scoped immutable receipts/history/reconnect, complete
write rollback, competing ready CAS one winner, all append-only tables update/delete
refused, terminal head no resurrection/delete, event+assignment rollback, exact
persisted ACK/replay/foreign conflict, lost ACK-write rollback and duplicate key
whole-UoW rollback. Connection reopen is not process/cluster restart proof.

## Actual adopter matrix / conformance

| Gate | Owner / required actual behavior |
|---|---|
|CR11-01|12/11 definition provider verifies full asset bytes hash listed in current published reviewed ContentWrite, scoped title/age/source lineage; not a catalog ID/editorial note interpreted as safety|
|CR11-02|BE1/12 policy owners provide exact current per-child ages/membership/purpose-specific consent, source recall/rights, actual safety/material/prerequisite/adaptation review. Hold fences through own commit; no group mean/true-checkbox authority|
|CR11-03 source composition|BE1/P4 consumes scoped catalog projection in primary CMD-59 and CMD-45 assignment references, no duplicated endpoints/direct DB|
|CR11-03 outcome|BE1 consumer authenticates/dedups event ID+immutable exact body, accepts only scoped result refs with truthful attribution, returns exact ACK; no automatic child achievement/Teacher note/Child reflection/portfolio entry|
|Delivery/recovery|One explicit event attempt per call outside11 DB tx, at-least-once; concurrent redelivery safe only with REAL durable BE1 dedup. Lost/foreign ACK remains pending, no changed payload/new outcome/false save. No hidden worker scheduler/lease/default retry policy|
|Recall/intervention|Actual owner notice/cause and current gate prevents stale new start. Running invalidation retained, no claimed physical stop. Source/audience/adaptation changes need re-preparation/review as policy dictates|

Test actual published source ->group adaptation ->confirm ->start ->finish/skip/
interrupt ->BE1 result ACK, check exact source/effective snapshot hash and actor/
audience before/after states. Negative every child age, hazard/missing material,
unknown review/policy, recalled source, stale membership/revision, Child, duplicate/
conflicting key, concurrent edits/start/recall, partial result save, lost ACK/restart/
old event/wrong sink ACK. Missing reflection stays absent/NOT_OBSERVED per owning
contract, never negative assessment; group outcome not individual skill evidence.

Actual11 can be verified with reviewed activity/library and synthetic teaching
session on adopted owners; no live Sketch/video generation needed. If selecting AI
ranker later, approve provider/profile/license/budget/environment separately; no old
Wan/L4/TTS or preference/readiness assumptions inherited. Preserve sanitized source/
command/environment/receipt/JUnit evidence per case; never tracked child data/secrets.
