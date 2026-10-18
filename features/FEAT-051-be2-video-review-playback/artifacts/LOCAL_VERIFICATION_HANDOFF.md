# BE2-09 C4 — receiver handoff and delayed verification batch

Branch feature/be2-08-14; revision1 P1–P4. Internal implementation/local preparation
complete; actual external verification/adoption pending. No push/merge/deploy and
no requirement to create a new chat. Current implementation is additive and does
not modify08/BE1/shared05 tables/migrations or production app registration.

C4b: actual own SQL21 now PASS under separate environment approval, PG17.11,
source unchanged and cleanup verified. Current evidence E07
notes/C4B_ACTUAL_POSTGRES_20261018.md. Local pack intentionally still SQL-disabled;
its collection-only status is not a retraction of separate actual SQL evidence.

## What successor gets

- Domain exact subject/head/audience/decision, deterministic invalidate/rebind/
  archive, fresh review required after restored eligibility. Pin hash is not byte
  hash; policy pin change alone does not prove script edit.
- Candidate current-authority/own UoW/BE1 bridge ports; review-write, lifecycle and
  playback services with closed current-gate and original-key recovery semantics.
- Own PostgreSQL rows/codec/schema/migration +prepared SQL tests. History/events/
  receipts immutable; new head monotonic; pending playback terminal transition only.
- Strict injected CMD-41/42 HTTP, safe projections/errors, no default auth/routes,
  no access token/URL or alleged current playing. HTTP_CONTRACT_HANDOFF.md is the
  payload/precondition/identity/resolver/error guide.
- One-batch local runner with exact inventory/source closure/JUnit classifier,
  acceptance audit and explicit dependency owner register. Full status is in
  status/STATUS.md; current measured SQL evidence E07 and local component evidence E06.

## Run all local checks once

From repo root using the existing backend interpreter (Linux equivalent path is
backend/.venv/bin/python):

```powershell
backend/.venv/Scripts/python.exe features/FEAT-051-be2-video-review-playback/src/run_component_checks.py
```

No dependency install/server start/provider/SQL writes. Runner drops VR09/KV08 SQL
opt-ins in subprocesses and SQL only collects. Output under ignored
.runtime/video-review-component/<UTC-run>/ contains summary, collection/process
logs and own/regression JUnit. PASS requires exact pinned node names/hashes (not
counts only), no duplicates/missing/skipped/errors, approved frozen plan, unchanged
source closure and successful Ruff/Mypy/architecture/harness/security/diff checks.
Collection-only SQL status is COLLECTED_NOT_RUN, never actual SQL PASS.

Do not edit pins just to force green. A legitimate test addition requires review
and new exact inventory/evidence. Source inventory covers backend/transitive fixture
files, feature runner helpers/manifests and governance scripts; mutable evidence/
status prose excluded. Summary is LOCAL_COMPONENT_ONLY/full_card_complete=false.

## Own PostgreSQL batch — current completed; isolated rerun procedure

Current21 actual cases PASS under approvals/LOCAL_POSTGRES_APPROVAL.md. Temporary
environment removed, no live DB retained. Instructions below are for reproducing
in an explicitly authorized isolated environment; not auto-provisioning authority.

Do not start or create a database from the local pack. After owner approves a new
dedicated disposable loopback PG17 vr09_* database (length>=12), supply credentials
privately through VR09_TEST_DATABASE_URL, driver postgresql+psycopg, and explicit
VR09_TEST_ALLOW_SCHEMA_DDL=1. Never echo connection values or reuse08 opt-in.

In backend, run the21 collected tests in tests/integration/video_review/test_owned_sql.py
with the same existing interpreter, JUnit and sanitized log in ignored runtime.
Capture source hashes/exact collection before, re-enumerate after, classify the
actual JUnit with the local pack's same exact-node classifier. Only0 failures,
errors and skips +unchanged exact source inventory constitutes OWN09_SQL_PASS.
The local runner is deliberately SQL-disabled; do not modify it to inherit opt-ins.

Fixture refuses existing schema, checks PG17 and only creates own video_review
schema using frozen migration. Teardown drops exact created tables/functions/schema
without CASCADE; never broad DB deletion or other-owner writes. Cases cover frozen
tables, scope/receipts, rollback, initial/lifecycle CAS races, reconnect/pool dispose,
all append-only tables update/delete, head/approval guards, playback unique key,
intent+event rollback and terminal receipt preservation. Review actual failures,
especially PG trigger/transaction behavior; collection is not proof they pass.

## Actual adapter conformance — owners BE1/07/08/14/P4

| Gate | Owner/action | Required concrete proof |
|---|---|---|
| CR09-01 |08/09 +P4 agree canonical head/read/CAS and combined DATA-27 projection | Exact08 final bytes/lineage to09 subject digest/head, no immutable08 review revision rewrite; review revision independent of run/job/session |
| Current identity/eligibility |BE1 +07/08/14 | Authenticated Teacher action/scope, current source/moderation/publication/usage/purpose-specific consent/profile/rights/recall, locks/fences held through commit/effect; missing adapters closed |
| Source invalidation |07/08 +09 | Authenticated cause/version/context/audience notice; same-key replay; old head archived; new empty head; policy-pin change not mislabeled media edit; actual revocation fence |
| CR09-02 |BE1 session/access +P4 | Exact original key/body authenticated receipt, expected-session CAS, dedup and atomic/recoverable grant/session effect; never two sequential commits sold as atomic |
| Gateway each-use |BE1 access/P4 | Unauthorized/old ref/fetch/range/resume denied after current revoke/consent/grant change; late dispatch/start race blocked; no stale URL bypass |
| Recovery |BE1 bridge +own SQL | Lost intent/commit/start ACK, lookup outage, known absence, late/foreign/malformed receipt, reconnect/restart, changed-body conflict, no new key/repeat effect/false playing |

Own SQL PASS is not adoption of any row in this owner matrix. Actual bridge.start
must be outside09 DB transaction and current checks valid at
effect. Guard acquisition order is owner fences ->own store lock. Recover original
historical subject under original backend recovery authority, not by substituting
current content or reviving old approval. A receipt remains historical; new access
must still pass current gateway. Pending known-absent effect needs explicitly
adopted scheduler/reconciliation, never implicit redispatch from duplicate POST.

Run both reviewed-library positive (no Sketch dependency) and generated08 artifact
when its provider is selected/approved. Negative matrix: child/wrong org/session/
audience; failed moderation/recall/consent/grant; same bytes edited script/pin;
changed bytes/version; old review/ETag; concurrent invalidation/start/fetch; stale
capability/old ref; lost ACK/replay/foreign receipt. Record actual expected vs
observed state/revisions/effect count and final byte digest, not just HTTP200.
These checks need REAL adopters; no mock pass can close their gates.

## Combine later with08 Lightning/runtime tests

Keep08 own SQL11/local459 and09 local proof separate. Consult FEAT-050 artifacts/
LOCAL_VERIFICATION_HANDOFF.md and ACCEPTANCE_AUDIT.md. Before any actual generation,
approve provider/model/profile/license/encoding/decoder/resource budget/environment;
no assumption Wan/L4/TTS/35–40s from old demos. Batch source-pinned cases for:

1. Actual08 library/generated media validation, size/duration/container/hash/rights/
   context gates, provider timeout/error/cancel/late result and accepted cleanup.
2.09 exact session review of those final bytes, explicit start and independent
   revisions, actual current gateway scope and edit/revoke/fetch/range/resume.
3. Foundation/BE1/08/14 actual submission/finalization/copy-journal control/recovery
   and observer acceptance; isolated failed cases don't silently advance sessions.

Collect sanitized source/command/environment profile (no secrets), exact JUnit/
receipts and quality review per case. No runtime output staged in repo. Lightning
success without actual BE1/access adoption is not integrated09 acceptance. Update
full-card status only after own SQL +required owner/runtime conformance and sign-off.
