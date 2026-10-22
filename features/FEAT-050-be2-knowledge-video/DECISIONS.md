# BE2-08 decisions

## Claude D3 rereview 4 — completion and descriptor gates — 2026-10-21

The report verified the pinned D3 inputs and found a completion-time budget P2 plus four P3 items. BE2-08 scope Rev3 clarifies the completion-time D4 gate, source validation order, descriptor FOUND/ABSENT/UNAVAILABLE, operation-journal identity and temporary/audit interpretation. These are scope requirements/gates, not implemented behavior.

D3 C1-A/C2-A remain selected. BE1 descriptor/quarantine/accepted-reference adoption, exact BE2-08 manifest and supplemental S/F/schema approvals remain pending. No code/test/approval/card acceptance changed.


## Owner D3: video participant and lifecycle CR - 2026-10-21

Direct owner C1-A/C2-A conditions are preserved in FEAT-057 evidence/notes/CROSS_LANE_UOW_OWNER_DECISION_D3_20261021.md, SHA256 C1799417AFD2DDB989D6C888A8B3F9702D4A6B4DC2A8B90637DBD6E11C3AE54C. D1/D2 remain applicable. BE2-01 owns every UoW; BE2-08 writes only its video rows without begin/commit/rollback authority.

Budget hold keeps both job/run QUEUED with no video budget state; attempt_id stays null until S. B-stale atomically commits job SUCCEEDED/STALE/result refs/receipt, terminal stale run without artifact/ready state and verified-owned-ref keep-private intent. Accepted artifacts stay protected; BE1 artifacts adoption remains pending.

The successor plan/CROSS_LANE_BE2_08_SCOPE_REV2_DRAFT_20261021.md includes model, codec, save terminal guards, _receipt, full retry/fail/block/timeout/stale transitions and versioned public projection. It corrects old A/B-only domain/codec exclusions without changing those historical bytes/approvals. Independent review, schema-specific scope where needed, exact file manifests and supplemental S/F approvals are pending. No source/test/schema/official approval or card acceptance change is made.


## Owner D1: BE2-08 lifecycle participant limits — 2026-10-21

For the selected A/S/B/F model, BE2-01 owns and opens the foundation UoW.
BE2-08 participates only by mutating its own video rows for start, retry with a
new attempt, fail, cancel, and timeout; it cannot begin, commit, or roll back the
enclosing UoW. Reconciler and outbox-driven job changes must enlist this
participant. Rejected finalization uses a separate foundation reject commit for
quarantine/cleanup intent. Lock order is job → video run → source-fence rows in
stable key order. The proposal is in FEAT-044 scope revision 3 and the owner
receipt is FEAT-057 `evidence/notes/CROSS_LANE_UOW_OWNER_DECISION_D1_20261021.md`.

This direction is not implementation approval and does not amend the current
BE2-08 addendum or approval. A/S/B/F details need independent review and
separate supplemental approval. BE2-08 remains IN_PROGRESS; CR08-01 is open;
X01 is PARTIAL, X05d BLOCKED, X05c/CR09-02 open. No source, test, schema,
acceptance, provider, database, Modal, Lightning or runtime action follows.

## FEAT-057 implementation-scope addendum — 2026-10-21

- Approved addendum: plan/CROSS_LANE_BE2_08_SCOPE_DRAFT_20261021.md
- Approval record: approvals/TASK_APPROVAL.md
- Proposed scope has two separate atomic commits: submission and finalization, with external generation between them. CR08-01, BE2-07 source fencing, BE2-01 routing, and BE2-14 phase/authorization/accounting bindings remain explicit gates.
- Owner approved the exact scope SHA256 6A195B6F3C9901621D268CF26B34AA217EECAFE66FA5922BD066149E6A9BC0B0. The verbatim approval is in approvals/TASK_APPROVAL.md. The minimal execution file subset must be recorded before edits.
- Existing component/runtime status and the approved card-local plan remain unchanged; this approval-recording step does not change BE2-08 source/tests.

## FEAT-057 cross-card owner response — 2026-10-21

The user confirmed they own the affected cards and approved the G0 proposal
with `Chốt theo đề xuất`. For BE2-08, B1–B4 and B7 are `ADOPT_WITH_CHANGES`:
require the BE2-07 exact-source fence through finalization; keep submission and
finalization as distinct atomic boundaries with provider work between; adopt the
specified replay/winner and late-result behavior; use only the typed BE2-08
`VideoWorker` route with unknown types failing closed; and enforce phase-specific
policy/kill checks separately from worker/provider execution authorization and
budget/concurrency boundaries. The dispatch identity mapping must be
contractually stable or separately versioned. See FEAT-057's
`evidence/notes/G0_CARD_OWNER_DECISION_BALLOT_20261021.md`.

This adopts contract direction only; it does not approve new BE2-08
source/schema/test changes or alter the existing card-local approval. Actual
CR08-01 bridge implementation and runtime gates remain open; BE2-08 stays
`IN_PROGRESS`.

## C4b — approved actual own SQL, not integrated completion

Direct08 environment approval permits disposable loopbackPG17/own11 SQL tests and
cleanup. Portable archive identity verified, existing Python reused, nonsuperuser
runner has no CREATEDB/CREATEROLE. All11 PASS without source fixes; temp cluster/
data/binaries/archive/secrets removed. Own SQL is not foundation/BE1 atomicity.

## C4 — one local receipt, separate actual gates

Own runner reuses14 strict JUnit classifier but keeps correct own node parser:
normalize Windows path only, not backslashes in parameter data. Re-enumerate
source closure, pin exact inventory, reject skips/identity changes. Never run SQL
fixtures through this pack, even with inherited opt-in. Existing Pillow fully
decodes authored synthetic GIF fixtures only, no production decoder/codec decision.
Local pass/audit/runtime sheet do not complete actual SQL/generation/adoption.

## C3b — video consumes14 hook protocol, not deletion authority

Script maps to existing input copy kind; scope/provider profile explicit, not
guessed session/model refs. Original lineage producer is not source/coverage proof.
Guarded hook requires actual source/current claim/authority adoption; effect errors
remain pending without retry loop. Receipt availability is not verified deletion.
No generation inventory bootstrap with fabricated data-request context. Existing
shared14/foundation contracts unchanged. Update checkpoint docs together after test.

## C3a — ambiguous ACK is pending, not permission to repeat or delete

Owned worker outcomes are not job mutations/ACKs. Stage recovery queries original
journal; finalization recovery queries actual authenticated original-scope receipt
before current teaching eligibility. Prior accepted receipt is historical fact,
not current playback permission. No guessed cleanup after ambiguous commit.
Quarantine stays pending and actual processing must atomically fence accepted
references against concurrent finalization. Fixture validation cannot establish
durable atomicity, copy deletion or current authority. CR08-01 remains open.

## C2c — preparation is not completion

Explicit strategy ports/pure media profile/byte and decoded-report checks under
existing P2/P3 plan. reviewed_library independent of generation model; no silent
fallback/TTS. Original operation key binds pin/job/attempt, not progress revision.
PreparedVideoMedia uncommitted only; P3 owes actual current completion fences and
accept/quarantine bridge. Test decoder/provider/authority fixtures not actual
generation/decode evidence. No profile/codec/duration production defaults selected.

## C2b — closed snapshot and caller-bound own SQL participant

HTTP never guesses job history: adapter supplies a strict complete snapshot,
revalidated against run/current lease and normalized before serialization. Router
requires explicit verified session identity and body-size config; not registered
in production. No model/provider/server selection added.

Own knowledge_video branch stores only opaque run lineage/receipts; no cross-owner
FK or actual job creation. Connection-bound participant cannot commit itself.
CR08-01 remains open; actual atomic bridge and current owner bindings not inferred.
SQL tests are prepared11/NOT_RUN; no previous card provisioning approval reused.

## C2a — actual submission adapter intentionally not invented

Guarded create depends on candidate context-bound held owner lease and atomic
submission port. Process-local fixture maps stage only job/dispatch INTENTS.
No production adapter calls domain.create_job to bypass foundation ownership,
and no sequential pair of commits is labeled atomic. CR08-01 captures the gap.
P2 remains partial; no live HTTP route or owned SQL migration yet.

## C1 — owned candidate only

Typed DATA-27 pre-review subset, pin canonicalization and pure run transitions
implemented under approved P1. No upstream DATA-26 schema altered. Dependency
register captures owner/session/foundation bridge/kill/consumer/provider adoption.
Actual P2/P3 authority and decoder/job effects are not inferred from pure tests.

## 2026-10-18 — D01 planning only

Follow receiver handoff order12 →14 →08 →09 →10 →11 →13. Feature050 is card08,
not a reassignment of sender07. Plan revision1 pending owner approval.

## D02 proposed execution boundary

P1–P4 implement/test owned component, prepare P5 runtime batch. Unknown provider/
rights/profile/dependency/provisioning choices are separate activation gates.
Full08 includes actual generation evidence, not only library or fixture success.
No historical Wan/L4/duration/TTS choice is adopted by this document.

## D03 contract safety

Foundation shared migrations/contracts remain immutable without coordinated CR.
Real BE1/P4 wiring remains deferred, not waived acceptance. Atomic submission and
generation-safe cancellation must not be simulated as actual runtime guarantees.

## Owner-directed shared UoW participant and artifact-read disposition — 2026-10-21

The owner directed that BE2-01 owns the foundation UoW and BE2-08 participates
through its own connection-bound row operations without beginning, committing or
rolling back the enclosing transaction. Submission and finalization remain two
separate commits, with generation outside both. BE2-07 source validity is checked
in the finalizer UoW only if the source and finalizer share the transactional store;
otherwise X01 remains PARTIAL.

BE2-08 will publish a public, read-only finalized-artifact model for BE2-09.
BE2-09 consumes that model and owns review state; it must not write BE2-08 rows.
Exact read-model fields and visibility semantics still require contract review.
The new foundation UoW scope is a draft only:
../FEAT-044-be2-ai-job-foundation/plan/CROSS_LANE_FOUNDATION_UOW_SCOPE_DRAFT_20261021.md
(SHA256 B456DEEDF5F892F328E7AEEFF442BC82281400A994EB5A74D791C13856FAB9B0).
It does not amend the approved BE2-08 addendum or authorize implementation. A
BE2-08 participant manifest and supplemental approval are required before its
source is edited. CR08-01 remains open; late-result winner/quarantine details and
reservation timing are not decided here. X05d remains BLOCKED; X05c/CR09-02
remains open. No source/test/status/acceptance changed.

## Read-only artifact model scope supplement — 2026-10-21

Owner direction requires BE2-08 to publish a read-only finalized-artifact model for BE2-09. A separate draft is at plan/CROSS_LANE_BE2_08_ARTIFACT_READ_MODEL_SCOPE_DRAFT_20261021.md (SHA256 F24823A192A90F11649871348AC0C539C3E63501AAA3A75C21DBC36EB7F15FA1). Exact fields, principal/org/session visibility, read-after-commit behavior, and historical/superseded semantics remain pending independent review and owner approval. The existing approved BE2-08 addendum is unchanged; this supplement authorizes no source/schema/test edit, card acceptance, playback access, or runtime. X05d remains BLOCKED and X05c/CR09-02 OPEN.

## Artifact read-model cross-reference review — 2026-10-21

The current read-model supplement still references foundation UoW scope revision 2 and its proposed receipt identity is not yet supported by a BE2-08 row or public cross-card query. Preserve the supplement unchanged until foundation scope revision 4 passes independent review. Then refresh the reference and resolve receipt provenance, exact artifact identity, and stale/superseded behavior through an owning-card decision. No read-model implementation or approval is implied; BE2-09 remains read-only.

## Cross-lane UoW owner D2 — 2026-10-21

The owner selected a distinct terminal stale representation for BE2-08 VideoRun when foundation reports SUCCEEDED with ResultDisposition.STALE; it carries no artifact or ready-for-review state and requires a versioned BE2-08 CR. VideoRun attempt_id is bound only at S; retry clears the previous attempt_id while returning the run to QUEUED. Attempt number stays foundation-owned. This is design direction only; no BE2-08 source, schema, approval, or acceptance change is authorized. See FEAT-057 evidence/notes/CROSS_LANE_UOW_OWNER_DECISION_D2_20261021.md.


## Owner adoption of BE2-VIDEO-LIFECYCLE/1 — 2026-10-22

The owner adopted the typed transaction-bound A/S/B participant and identity-failure behavior under the hash-pinned FEAT-057 scope Rev2. BE2-08 writes only BE2-08 rows on the BE2-01-owned transaction; no application port exposes SQL. The durable BE2-07 source fence is expressly separate and X01 remains PARTIAL until a fence held through finalization is proven. The three owner approval manifests were verified before source/test edits. PostgreSQL 17 persistence evidence remains pending. This does not change FEAT-050 card acceptance/status.
