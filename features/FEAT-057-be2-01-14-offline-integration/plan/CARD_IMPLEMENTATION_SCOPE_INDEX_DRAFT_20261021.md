# FEAT-057 card implementation scope index

## Rereview 4 candidate successor set - 2026-10-21

Latest candidates: FEAT-044 foundation scope Rev7, budget CR Rev2, separate budget schema CR, stale CR Rev2; FEAT-050 BE2-08 scope Rev3; FEAT-049 BE2-14 scope Rev3; FEAT-057 slice plan Rev8. Exact hashes are pinned in the plan and next review-input manifest.

Claude closed the previous two P2 items in draft and raised NEW-1 for completion-time BUDGET_EXCEEDED plus NEW-2..NEW-5. D4 remains pending. These drafts do not expand frozen approved exact-hash subsets and do not authorize source, tests, schema, migrations, S/F or runtime.


## Latest candidate scopes after owner D3 - 2026-10-21

D3 C1-A/C2-A is design direction only. Latest candidates: FEAT-044 foundation Rev6 and budget/schema/stale CRs, FEAT-050 BE2-08 scope Rev2, FEAT-049 BE2-14 scope Rev2, FEAT-057 slice Rev7. They need independent review, missing contract adoption and supplemental S/F/schema approvals with exact file manifests.

The approved exact-hash fields below retain authority only for their historical bounded subsets. They do not approve the successor lifecycle/domain/codec/schema expansions. Slice Rev7 explicitly records Rev4/erratum/later divergence. No governing approved field is silently promoted to a new draft.

X01 PARTIAL; X05d BLOCKED; X05c/CR09-02 OPEN; X09-08 NOT_IMPLEMENTED; budget terms/max duration/deadline action and BE1 adoption pending. All official approvals/source/tests remain unchanged.


- Status: OWNER_APPROVED_SCOPES / BE2-01_MANIFEST_FROZEN / OTHER_MANIFESTS_GATED
- Prepared: 2026-10-21 (Asia/Saigon)
- Governing integration plan: CROSS_LANE_X01_X05_SLICE_PLAN_DRAFT_20261021.md, revision 4
- Governing plan SHA256: 6AF69E07E7FC51BD6AAA992A703FBE97AC2BC8E588FEC9F8735FBF74E88C6601
- Scope: proposed card-owned changes for BE2-01, 07, 08, 09 and 14.

The five addenda remain byte-frozen scope records with their original DRAFT headers;
the later direct owner approval is recorded in each owning card's official approval
file. They do not amend frozen card-local plans, accept a card, change card status,
authorize publication, or resume Modal/Lightning/runtime work. Offline implementation
is approved only within each exact addendum and its frozen execution manifest.

Owner D1 has since selected paired lifecycle model A for BE2-01/08. The separate
FEAT-044 UoW scope revision 3 is not included in any of the five existing
addenda or execution manifests; its S/F boundaries require independent review
and new supplemental approvals before implementation. The existing BE2-01
typed-dispatch approval does not cover this work. FEAT-057 slice-plan revision
4 remains unchanged pending an explicit reviewer disposition on the A/S/B/F
delta.

## Proposed ownership map

| Work | Owning card | Proposed ownership boundary |
|---|---|---|
| Typed dispatch selection for BE2-08 jobs | BE2-01 / FEAT-044 | Select and route the existing foundation dispatch envelope by an adopted job type. Do not construct or mutate BE2-08 run state; do not edit BE2-08 ports. |
| Exact source identity and source-side currentness | BE2-07 / FEAT-056 | Expose and verify the producer-owned exact bundle/source identity and its currentness facts. Do not claim the process-local coordinator is a durable cross-card fence. |
| Video submission, worker admission and finalization | BE2-08 / FEAT-050 | Own video run and artifact records and participate through authorized foundation boundaries. Keep submission and finalization as separate commits with external generation between them. |
| Canonical review head / DATA-27 projection for exact output | BE2-09 / FEAT-051 | Own review projection, history and review persistence. Never write BE2-08 rows or migrations. |
| Current policy and accounting contracts used by video | BE2-14 / FEAT-049 | Own policy phase decisions, current-use guards, and budget/concurrency reservation/accounting contracts. BE2-08 remains the consumer and worker orchestrator. |
| Cross-card composition and edge evidence | FEAT-057 | Own integration composition/adapters and X01/X05/X09-08 tests in backend/src/sketch2life/infrastructure/cross_lane/ and backend/tests/integration/be2_cross_lane/. These paths are not part of any one card's allowed file list. |

## Dependencies and safe implementation order

1. Keep each approved addendum's exact SHA pinned. Freeze the minimal execution-file
   subset in its official approval record before touching that card's code. BE2-01's
   first subset is recorded below; the other subsets remain gated by their unresolved
   contracts.
2. Resolve the producer currentness contract between BE2-07 and the BE2-08 finalizer.
   The source resolver currently proves an exact read. The existing fixture coordinator
   is process-local and cannot satisfy the held-through-finalization claim.
3. Resolve BE2-14 phase mapping and the separate execution-authorization and budget
   reservation/settlement contracts before BE2-08 can enable generation.
4. Add BE2-01's typed route only against an adopted BE2-08 entrypoint and a verified
   persisted-job lookup. Do not add source pins or idempotency data to the broker
   envelope by assumption.
5. Implement BE2-08's submission/finalization boundaries and source/policy gates;
   then let FEAT-057 compose the real card-owned ports in an offline integration test.
6. Implement the BE2-09 CR09-01 exact-artifact review projection only after its
   artifact identity mapping is adopted. X05d remains blocked until an already-adopted
   current-source resolver/fence exists. Do not pull X02 or CR09-02 into this slice.

This is an ordering proposal, not a claim that each gate is already satisfied. Work
may stop at any gate and must report the edge as PARTIAL or NOT_IMPLEMENTED when its
required contract or evidence is missing.

## Non-overlap rules

- Only BE2-01 may change the foundation dispatch worker or its unit tests.
- Only BE2-07 may change the knowledge-bundle producer service/contract or its tests.
- Only BE2-08 may change video creation/worker/finalizer code, video-owned rows and
  video-owned migrations.
- Only BE2-09 may change review-owned rows, review projection, review HTTP, and review
  migrations. DATA-27 projection must reference the exact BE2-08 artifact identity.
- Only BE2-14 may change policy-use/accounting decision code, policy-owned rows, and
  policy migrations.
- Shared contract files are edited by their owning card only, with the consumer card
  reviewing the exact payload and failure semantics. FEAT-057 does not acquire card
  ownership by composing adapters.
- Any file outside a card addendum's manifest, any new migration, or any change to a
  shared versioned contract stops implementation for a revised scope and approval.

## Required evidence before claiming the slice

- Card-owned unit/contract tests and each card's existing required offline regression.
- FEAT-057 composition tests on one pinned source tree, with separate results for X01,
  X05 and the BE2-08-only X09-08 route.
- Race/replay/lost-ack tests at each actual commit boundary; tests must not collapse
  external generation into a database transaction.
- Source and file hashes, test commands/results, validator receipts, and explicit
  mapping of every acceptance row to evidence.
- No Modal, Lightning, provider, server, real database, or runtime claim is authorized
  by these drafts. Such work retains its existing separate environment gates.

## Draft set

| Card | Proposed scope | Proposed approval record |
|---|---|---|
| BE2-01 / FEAT-044 | FEAT-044-be2-ai-job-foundation/plan/CROSS_LANE_BE2_01_SCOPE_DRAFT_20261021.md | FEAT-044-be2-ai-job-foundation/approvals/CROSS_LANE_BE2_01_IMPLEMENTATION_APPROVAL_DRAFT_20261021.md |
| BE2-07 / FEAT-056 | FEAT-056-be2-knowledge-script/plan/CROSS_LANE_BE2_07_SCOPE_DRAFT_20261021.md | FEAT-056-be2-knowledge-script/approvals/CROSS_LANE_BE2_07_IMPLEMENTATION_APPROVAL_DRAFT_20261021.md |
| BE2-08 / FEAT-050 | FEAT-050-be2-knowledge-video/plan/CROSS_LANE_BE2_08_SCOPE_DRAFT_20261021.md | FEAT-050-be2-knowledge-video/approvals/CROSS_LANE_BE2_08_IMPLEMENTATION_APPROVAL_DRAFT_20261021.md |
| BE2-09 / FEAT-051 | FEAT-051-be2-video-review-playback/plan/CROSS_LANE_BE2_09_SCOPE_DRAFT_20261021.md | FEAT-051-be2-video-review-playback/approvals/CROSS_LANE_BE2_09_IMPLEMENTATION_APPROVAL_DRAFT_20261021.md |
| BE2-14 / FEAT-049 | FEAT-049-be2-ai-policy/plan/CROSS_LANE_BE2_14_SCOPE_DRAFT_20261021.md | FEAT-049-be2-ai-policy/approvals/CROSS_LANE_BE2_14_IMPLEMENTATION_APPROVAL_DRAFT_20261021.md |

The owner approved all five exact plan hashes on 2026-10-21. Verbatim responses are
recorded in the owning official approval files: BE2-01 in PHASE_B_TASK_APPROVAL.md;
BE2-07/08/09/14 in each card's TASK_APPROVAL.md. Preserve those records. Before any
source edit, record the minimal exact file subset from each approved candidate list;
new/unlisted paths require renewed approval.

## Frozen execution subset and current blockers — 2026-10-21

| Card | Frozen execution subset | Current state |
|---|---|---|
| BE2-01 | Modify `backend/src/sketch2life/infrastructure/ai_jobs/worker.py`; add `backend/src/sketch2life/infrastructure/ai_jobs/typed_dispatch.py`; add `backend/tests/unit/test_ai_job_video_dispatch.py`. Run the existing B5 worker test as regression; do not edit it unless the new behavior makes it fail. | Typed route implemented; 79 focused offline tests pass. Persisted-job-to-VideoWorker composition is still unproven, so X09-08 remains `NOT_IMPLEMENTED`. |
| BE2-07 | No source edit selected yet. Candidate exact-export/currentness paths and tests are already in the approved addendum. | The producer can re-resolve the exact pin, but the existing process-local coordinator cannot hold a durable fence through BE2-08 finalization. Keep X01 `PARTIAL`. |
| BE2-08 | No source edit selected yet. | CR08-01 lacks a foundation-owned shared UoW/recovery entrypoint in the approved file boundary. Do not claim atomic submission/finalization or implement split commits as atomic. |
| BE2-09 | No source edit selected yet. | No adopted public BE2-08 artifact-read mapping is available to bind CR09-01 safely. X05d stays `BLOCKED`; X05c/CR09-02 stays open. |
| BE2-14 | No source edit selected yet. | Existing generic current-use/accounting services do not define a BE2-08 worker-execution grant or reservation expiry/renewal. Keep generation authorization gated; no fixture becomes a provider grant. |

The same exact BE2-01 subset and stop conditions are recorded in
`features/FEAT-044-be2-ai-job-foundation/approvals/PHASE_B_TASK_APPROVAL.md` and
`evidence/notes/APPROVED_SCOPE_EXECUTION_MANIFEST_20261021.md`. No other card-owned
source or test file may be edited until its own minimal subset is recorded and every
blocking contract in its approved addendum is resolved within that scope.


## Independent UoW review update — 2026-10-21

Revision 4 remains byte-frozen at its recorded SHA. The owner-supplied independent
review returned CHANGES_REQUIRED. Corrections are in
CROSS_LANE_X01_X05_PLAN_ERRATUM_20261021.md (SHA256
7530294B18B30616EB9A968ABF0AD227C661294500CD0789A7EC514D54E5FE39)
and the new BE2-01 UoW scope draft
features/FEAT-044-be2-ai-job-foundation/plan/CROSS_LANE_FOUNDATION_UOW_SCOPE_REV2_DRAFT_20261021.md
(SHA256 39B0FD5958D2C298460F7605A7F73E8BDC7BC9D269B6399822FD2A2EAAC4DDC4).
The separate BE2-08 finalized-artifact read model supplement is
features/FEAT-050-be2-knowledge-video/plan/CROSS_LANE_BE2_08_ARTIFACT_READ_MODEL_SCOPE_DRAFT_20261021.md
(SHA256 F24823A192A90F11649871348AC0C539C3E63501AAA3A75C21DBC36EB7F15FA1).

At the time this index review update was recorded, the start/failure lifecycle
choice remained pending; the later owner D1 selection A is recorded at the top
of this index and supersedes that state. These drafts do not extend the five
already approved file manifests. Current BE2-07 scope cannot provide a shared-
store held fence, so X01 remains PARTIAL by default. No source, test, approval,
schema, migration, status, acceptance, or runtime permission is changed by this
index update.

## Latest UoW review successor candidates — 2026-10-21

Claude rereview 2 returned CHANGES_REQUIRED on scope Rev3. Review response: FEAT-057 evidence/notes/CROSS_LANE_UOW_CLAUDE_REREVIEW2_DISPOSITION_20261021.md. New candidates are FEAT-044/plan/CROSS_LANE_FOUNDATION_UOW_SCOPE_REV4_DRAFT_20261021.md and FEAT-057/plan/CROSS_LANE_X01_X05_SLICE_PLAN_REV5_DRAFT_20261021.md. They remain DRAFT / awaiting independent rereview; do not extend existing card manifests or approvals. S/F require separate supplemental approvals. X01 remains PARTIAL; X05d BLOCKED; X05c/CR09-02 OPEN; X09-08 NOT_IMPLEMENTED.
