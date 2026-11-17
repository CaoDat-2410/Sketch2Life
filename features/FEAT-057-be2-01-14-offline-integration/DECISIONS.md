# FEAT-057 decisions

## PostgreSQL 17 persisted-flow verification — 2026-10-22

The approved BE2-07 → BE2-01 → BE2-08 integration fixture passed 9/9 on isolated loopback PostgreSQL 17.11. This is evidence for the already-approved A/S/B scope, not a new owner disposition or broader card approval. It does not close the durable source-fence gate or change X01 (`PARTIAL`), X09-08 (`NOT_IMPLEMENTED` in the edge registry), X05d (`BLOCKED`), X05c/CR09-02 (`OPEN`), or BE1 handoff (`NOT_SENT / NOT_READY`). See `evidence/notes/BE2_01_07_08_POSTGRESQL17_FLOW_TEST_20261022.md`.

The owner requested a full factual process handoff. Draft `evidence/notes/BE2_07_01_08_PERSISTED_FLOW_HANDOFF_DRAFT_20261022.md` is prepared as `NOT_SENT / NOT_READY_FOR_BE1_INTEGRATION`; it records the verified seam, evidence, and remaining fence gate. It creates no new decision, BE1 contact, implementation approval, or card acceptance.

## Owner request: prepare a complete BE2 cross-lane execution frame — 2026-10-21

The owner asked Codex to inspect the current evidence and plan the full BE2-01–14 behavioral graph so it can eventually be handed to BE1. The resulting draft is `plan/CROSS_LANE_END_TO_END_EXECUTION_FRAME_DRAFT_20261021.md`. This records planning direction only: it does not replace approved integration plan Rev2, extend existing exact card scopes, approve implementation, choose D4, close X05c/X05d, adopt BE1 artifacts, change card status/acceptance, or authorize runtime/Git publication. D1/D2/D3 C1-A/C2-A remain in force; D4 remains pending.

## Owner direction: prepare preliminary BE1 status handoff — 2026-10-21

The owner requested the factual, blocker-qualified handoff described in this checkpoint. It is prepared locally and NOT_SENT. It does not call or message BE1, assert the lanes are connected, request code integration against unadopted drafts, approve implementation, or change card status. The confirmed D3 C1-A state remains both job and run QUEUED while a durable hold is active; C2-A remains same-commit B-stale intent. D4/NEW-1 remains pending.


## Claude D3 rereview 4 — one owner decision pending — 2026-10-21

Claude verified all 81 manifest entries. The original P2s N-02/N-03 are closed in draft. NEW-1 is an uncovered BUDGET_EXCEEDED path after provider completion: current _decide_completion cancels and quarantines any ineligible result. D3 changed only _dispatch_one/start_attempt/retry_job. The report is preserved at evidence/notes/CROSS_LANE_UOW_CLAUDE_D3_REREVIEW_REPORT_20261021.md (SHA256 92BE229378A2DE06BAEED1FC6F675EA15FED338892A002A833F81F6972B44C12).

NEW-2 through NEW-5 are clarified in successor drafts Rev7/Rev2/Rev3 and slice plan Rev8. D4 completion-time disposition remains pending in evidence/notes/CROSS_LANE_UOW_OWNER_D4_COMPLETION_BUDGET_BALLOT_DRAFT_20261021.md. Recommended option A is only a recommendation. D3 C1-A/C2-A remain selected; no source/test/schema/approval/card acceptance changed.

X01 PARTIAL; X05d BLOCKED; X05c/CR09-02 OPEN; X09-08 NOT_IMPLEMENTED. Implementation is blocked pending D4 and prior adoption/supplemental approval gates. Modal/Lightning/runtime deferred.


## Owner D3: C1-A and C2-A selected with conditions - 2026-10-21

The direct decision is preserved in evidence/notes/CROSS_LANE_UOW_OWNER_DECISION_D3_20261021.md (SHA256 C1799417AFD2DDB989D6C888A8B3F9702D4A6B4DC2A8B90637DBD6E11C3AE54C). It supersedes C1/C2 PENDING in the historical ballot; D1/D2 and all prior report bytes remain intact.

C1-A: durable BE2-01 metadata, both job/run QUEUED, no budget lifecycle state, separate schema/new-migration CR, all three budget-denial branches, no wait-related dispatch loss/retry consumption, consent/kill cancellation unchanged, no provider during hold, fresh eligibility/reservation before execution. BE2-14 supplies deny/defer only. Units/limits/max duration/deadline action stay pending.

C2-A: authoritative B-stale commits SUCCEEDED/STALE/result refs/receipt, terminal stale run without artifact/ready state and descriptor-proven keep-private intent together. BE1 adoption of exact job/attempt descriptor cleanup in SUCCEEDED result_refs, fixed reason, deterministic event identity and accepted-reference protection remains pending; missing proof fails closed.

Scope Rev6, slice Rev7, BE2-08/14 successors and budget/schema/stale CRs cover completion/state tables and residual P3 corrections. All are candidates for independent review, not supplemental S/F/schema approval, implementation, card acceptance or completed integration. X01 PARTIAL; X05d BLOCKED; X05c/CR09-02 OPEN; X09-08 NOT_IMPLEMENTED; ENV deferred.


## Current checkpoint: Claude rereview 3 — 2026-10-21

D1/D2 remain the recorded owner design decisions. Rereview 3 returned CHANGES_REQUIRED. The D3 ballot is a proposal with C1/C2 still PENDING, not owner adoption. No suggested/preselected option or elapsed time constitutes consent. See evidence/notes/CROSS_LANE_UOW_OWNER_D3_BALLOT_DRAFT_20261021.md and the correction specification. No supplemental S/F approval or card acceptance is recorded here.

Earlier dated entries below are historical; this proposal does not reopen the already chosen D1/D2 directions.


## Owner D1 disposition for shared UoW lifecycle — 2026-10-21

The owner selected model A and added the conditions in
`evidence/notes/CROSS_LANE_UOW_OWNER_DECISION_D1_20261021.md`. BE2-01 owns and
opens the UoW for A/S/B/F, including reconciler retry/timeout/cancel and
outbox-driven job transitions; BE2-08 is limited to its own video rows and may
not control the enclosing transaction. Rejected finalization writes the
quarantine/cleanup intent in a separate foundation reject commit. Finalization
rollback is infra-only and must recover explicitly. The selected scope lock order is
job → run → source-fence rows by stable key; Claude must verify it against the
actual lock paths.

The FEAT-044 scope successor is
`../FEAT-044-be2-ai-job-foundation/plan/CROSS_LANE_FOUNDATION_UOW_SCOPE_REV3_DRAFT_20261021.md`.
This is a design decision only: S/F require independent review and separate
supplemental approvals; no card approval, source, test, acceptance, or runtime
authorization is inferred. X01 stays PARTIAL; X05d BLOCKED; X05c/CR09-02 open;
BE2-14 budget unit/limit remain unprovided; Modal/Lightning/provider/runtime
remain deferred.

The current X01/X05 slice plan revision 4 and erratum have not been amended to
reflect S/F. Their exact divergence is an explicit item for Claude's
independent review before a successor plan or erratum is prepared.

## Card implementation scope package — 2026-10-21

Prepared five card-owned scope addenda for BE2-01, BE2-07, BE2-08, BE2-09, and
BE2-14. The owner approved each exact SHA and the official supplemental approvals
are now recorded in the card approval files. The ownership matrix, sequence,
no-overlap rules, and evidence gates are in
plan/CARD_IMPLEMENTATION_SCOPE_INDEX_DRAFT_20261021.md.

The approvals grant offline implementation within the exact addenda, subject to
recording a minimal exact file subset before edits and honoring each blocker. They do
not amend frozen card plans or change card acceptance/status. X05d remains BLOCKED,
X05c/CR09-02 remains open, and Modal stays deferred.

## First approved offline implementation checkpoint — 2026-10-21

BE2-01's frozen typed-dispatch subset is implemented and passes 79 focused
offline tests plus Ruff and strict mypy. The router preserves the original
envelope and fails closed for unregistered job types; this is only unit-level
route evidence and does not prove persisted job/admission composition or X09-08.
The four other approved card addenda remain gated by their specific missing
durable contracts. X01 remains PARTIAL, X05d BLOCKED, X05c/CR09-02 open, and no
card status/acceptance changes. See
`evidence/notes/APPROVED_SCOPE_EXECUTION_MANIFEST_20261021.md` and FEAT-044's
typed-dispatch evidence.

## G0 owner contract-direction response — 2026-10-21

The user clarified they own the affected cards and approved the proposed
contract dispositions with `Chốt theo đề xuất`: B1–B5 and B7 are
`ADOPT_WITH_CHANGES`; B6 is `BLOCKED` because no already-adopted current-source
resolver/fence was identified. This supersedes the preference-only/pending
wording in the preparatory ballot notes below. It adopts contract direction
only, not implementation approval or card acceptance. Card-owned source/schema/
test changes still require explicit approved scope. Keep X05c/CR09-02 open, X02
outside this slice, Modal deferred, X01 `PARTIAL`, X02–X09 `NOT_IMPLEMENTED`,
and all card statuses unchanged.

## Historical G0 ballot-preference state — superseded by direct owner response

- The repository owner approved the preferred ballot selections with the
  direct response `Chốt theo đề xuất`: B1–B5 and B7 are preferred
  `ADOPT_WITH_CHANGES` responses; B6 is `BLOCKED` unless an owner identifies an
  already-adopted current-source resolver/fence.
- At that point the ballot had not been routed and the owner had not yet
  clarified they owned the affected cards. The direct owner response recorded
  above supersedes this pending-response marker. Detailed implementation
  scope/approval remains pending in the owning features.
- Keep X05c/CR09-02 open, X05d conditional, X02 outside the slice, Modal
  deferred, X01 `PARTIAL`, and X02–X09 `NOT_IMPLEMENTED`. No card status,
  acceptance, source, test, or task approval changed.

## Historical G0 card-owner ballot preparation — superseded 2026-10-21

- Record the repository owner's preferred answer for each open G0 contract
  question in `evidence/notes/G0_CARD_OWNER_DECISION_BALLOT_20261021.md`:
  B1–B5 and B7 recommend `ADOPT_WITH_CHANGES`; B6 recommends `BLOCKED` unless
  the owner identifies an already-adopted current-source resolver/fence.
- This was the preparation state before the direct owner response above. The
  ballot was not routed externally. B1–B5/B7 dispositions and B6's blocker are
  now recorded in the owning-card DECISIONS files; exact implementation scope,
  evidence, and approval still need card-local records.
- Keep X05c/CR09-02 `OPEN`, X05d conditional, X02 outside this slice, and Modal
  deferred. No card status, acceptance, approval, source, or test changed.
- The ballot is pinned to plan revision 3 SHA256
  `5500B0CA5ED839C4FF5150D66FC19F2751F6C1F93261DE37BB1629747FF41C04` and
  adoption packet SHA256
  `8BD324DFA446E3EEBE976A5E1018F9141EE0FA20BB2C6C23F0BABDCA025C6D75`.

## G0 card-owner adoption packet prepared — 2026-10-21

- The bounded adoption packet for BE2-01/07/08/09/14 was prepared before the
  user clarified direct ownership. It remains local and was **not routed
  externally**; the direct owner dispositions are recorded above.
- Use `evidence/notes/G0_CARD_OWNER_ADOPTION_PACKET_20261021.md` against plan
  revision 3 at SHA256
  `5500B0CA5ED839C4FF5150D66FC19F2751F6C1F93261DE37BB1629747FF41C04`.
- The packet still lists the exact contract/version, ownership, immutable
  identity mapping, transaction/fence/recovery boundaries, allowed files, and
  evidence fields needed for implementation handoff. A missing contract detail
  remains a blocker; do not infer implementation approval from this packet.
- X05c/CR09-02 remains open; X05d may use only an already-adopted
  current-source resolver/fence; OD-ENV remains deferred. No source/test,
  approval, status, or acceptance change is authorized by preparing the packet.

## Historical G0 contract source review — updated by owner response

- Independent source review: `PASS` for the X01/X05/X09-08 direction at FEAT-057
  scope. The owner's direction-only dispositions are now recorded above;
  candidate ports and fixture behavior are still not durable integrated
  contracts.
- Existing candidates include exact BE2-07 bundle resolution, separate BE2-08
  submission/finalizer protocols, BE2-09 guarded review-write ports and BE2-08
  phase checks. Their current records leave source-fence adoption, durable
  cross-card UoWs, CR09-01/02 and BE2-14 worker/budget bindings open.
- The owning-card implementation records must specify finalizer receipt
  identity/replay scope, duplicate winner and late-attempt CAS semantics, plus
  how the typed dispatch route maps subject/session, source pin and idempotency
  from the persisted job and run. The foundation envelope does not carry those
  values directly.
- X05d is `BLOCKED`; no already-adopted current-source resolver/fence was
  established. X02 stays outside the slice. X05c/CR09-02 remains open;
  actual session/access is not claimed. OD-ENV remains deferred.
- The direction-only owner dispositions are recorded above; implementation
  approval, acceptance or runtime authorization is not granted here. X01 remains `PARTIAL`; X02–X09 remain
  `NOT_IMPLEMENTED`; card records are unchanged.
- Review receipt: `evidence/notes/G0_CONTRACT_REVIEW_20261021.md`.

## Current owner disposition for X01/X05 slice — 2026-10-21

- The owner directly responded `Chốt theo đề xuất` and confirmed they own the
  affected BE2 cards. B1–B5 and B7 are `ADOPT_WITH_CHANGES`; B6/X05d is
  `BLOCKED` because no already-adopted current-source resolver/fence was
  identified. X05c remains open; OD-ENV remains deferred pending a separate
  explicit resume instruction.
- These are contract-direction dispositions recorded in the owning-card
  DECISIONS files. Per-card implementation scope and approval remain separate;
  this record does not authorize source/test changes or Modal/runtime execution.
- Keep X01 `PARTIAL` and X02–X09 `NOT_IMPLEMENTED` until behavior and adopted
  boundaries are actually demonstrated. BE2 card status and acceptance remain
  unchanged.
- Verbatim decision receipt:
  `evidence/notes/OWNER_DISPOSITION_X01_X05_20261021.md`.

## Offline cross-lane integration — 2026-10-20

- The owner authorized FEAT-057-owned composition/adapters/tests on the existing
  integration branch; plan revision 2 and the approval addendum record exact
  scope and exclusions.
- Start with X01 (BE2-07 exact export → BE2-08 media preparation pipeline), using actual
  producer/consumer services and the BE2-07 fixture validity coordinator.
- Do not edit card-owned source/contracts or migrations. Missing/unadopted
  contracts remain `NOT_IMPLEMENTED`; no test-only substitute may be called an
  integration PASS.
- Offline/process-local evidence is not SQL, live runtime, provider/Lightning,
  card acceptance, or production adoption.
- X01 is `PARTIAL`: exact BE2-07 export consumption and stale-source rejection
  are tested through BE2-08 media preparation, but the foundation job/artifact
  commit boundary is not connected. X02–X09 remain `NOT_IMPLEMENTED`.

## Integration candidate — 2026-10-20

- Use a new branch, `feature/be2-01-14-integration`, based on the published task-7 integration branch `feature/be2-01-07`.
- Merge the complete `feature/be2-08-14` tip with history preserved; do not squash or cherry-pick the seven card areas.
- Resolve conflicts using current feature plans, approvals, contracts, tests, and source-register authority. Preserve both branch histories and record every material conflict disposition.
- Keep per-card status, acceptance limits, and external gates intact. A passing aggregate offline run is not full-card acceptance or runtime adoption.
- Run offline checks only. Live Lightning/provider work remains deferred until the user confirms Lightning is operating normally and separately requests that campaign.
- Do not merge to `dev`/`main` or claim a PR to `feature/be2-01-07`: that target already contains the source task-7 commit and the PR diff is empty.

## Integration branch name — 2026-10-20

- Following the owner's instruction, rename the local candidate branch from
  `feature/be2-01-14-integration` to `feature/be2-backend-ai-integration`.
- This is a naming-only change: preserve the same commit history, integration
  scope, evidence, and open acceptance/runtime gates.

## Administrative FEAT number collisions — 2026-10-20

- Preserve the existing feature directory names and all references pinned to them. The independent BE2 allocations reused four administrative FEAT numbers; the exact BE2-to-directory mapping is in `artifacts/FEATURE_ID_COLLISION_MAP.md`.
- Resolve references by BE2 card number plus full directory path. Do not rename reviewed plans, approvals, runners, or evidence as part of this merge.
- The FEAT-030 duplicate already existed in the task-7 baseline and is outside this integration's scope.

## Primary-session handoff synchronization — 2026-10-20

- Continue the existing approved FEAT-057 offline integration allocation; the
  handoff-sync request does not expand runtime, install, DB or acceptance scope.
- Keep exact old matrix/report snapshots under evidence/raw/handoff-sync-20261020;
  retain every per-card recheck receipt and label the latest environment blockers.
- F057-H01: after reproducing the real graph assertion failure, scope the
  foundation migration test to its exact owned head sets. Preserve test IDs,
  case count, skip rules and lineage checks. No product/migration source change;
  preserve the original foundation worktree and frozen A17 bytes.
- Old full source maps remain historical after the single uncommitted test delta;
  fresh focused evidence does not claim a complete 01–14 pack or runtime PASS.
- Main handoff: evidence/notes/PRIMARY_SESSION_HANDOFF_20261020.md. No per-card
  status/approval/acceptance change; no installation or Git publication.

## Offline environment gate — 2026-10-20

- Keep the shared backend venv read-only. Its missing Pillow and python-multipart prevent a complete 08–14 component pack.
- Do not create or install the candidate-local venv until the separately requested owner authorization arrives.
- The requested profile is the backend editable install with dev and image-admission extras only; do not add model/GPU extras or weights.
- Until prerequisites are complete, keep all runner results source-bound to the prior receipt and label this candidate snapshot NOT_RUN/ENVIRONMENT_BLOCKED. Do not mark cards DONE or the batch PASS.

## Cross-lane verification disposition — 2026-10-20

- Record the full unit/contract batch as not green: 6,839 passed, 22 failed,
  and 5 skipped. Keep its failure groups attached to the source-bound report;
  do not attribute them to the X01 adapter without a separate reproduction.
- The relevant single-command cross-lane regression is 296/296 passing, and
  the same count passes from the exact source ZIP after extraction. This is
  behavior evidence for the bounded offline slice only.
- The exact source ZIP also passed the same 296 tests in a hosted Modal CPU
  Notebook (Python 3.12.6; `pip check` clean). Receipt, JUnit, and log hashes
  are recorded in `evidence/metrics/CROSS_LANE_X01_MODAL_20261020.json`.
- Modal confirmation does not close X01's foundation job/artifact commit or
  cross-owner fence gap; X01 remains `PARTIAL`, X02–X09 remain
  `NOT_IMPLEMENTED`, and card acceptance/runtime state is unchanged.
- Keep X01 `PARTIAL` and X02–X09 `NOT_IMPLEMENTED`; no card acceptance or
  runtime readiness changes from these checks.
- Use the CPU-only Modal Notebook to reproduce the scoped test batch. A hosted
  Modal run is a separate result and remains NOT_RUN until the owner executes
  the notebook and returns its JUnit/receipt.

## Cross-lane residual contract review — 2026-10-20

- X04–X09 remain `NOT_IMPLEMENTED`. The current candidate has no adopted
  publication binding for both consumers, foundation finalizer output lineage,
  BE2-08-to-10 failure bridge, preset-to-foundation job adapter, per-consumer
  BE2-14 policy binding, or BE2-08/13 job-handler registry.
- Recommended order for owner/card adoption is X05 atomic BE2-01/08 finalization
  first, then X02/X04 source-publication delivery, then X07/X08/X09. The current
  FEAT-057 scope permits only adapters over existing public contracts; it does
  not authorize card-owned contract or implementation changes.
- Source review: `evidence/notes/CROSS_LANE_RESIDUAL_REVIEW_20261020.md`;
  source hashes: `evidence/metrics/CROSS_LANE_RESIDUAL_REVIEW_20261020.json`.
  No behavior tests or card status/acceptance changes resulted.

## Offline environment gate resolution — 2026-10-20

- The user's explicit reply “Authorize isolated venv install” is recorded in
  `approvals/LOCAL_ENVIRONMENT_APPROVAL_20261020.md` and supersedes the pending
  install gate above for this integration worktree only.
- Install the backend editable `.[dev,image-admission]` profile into the
  ignored candidate-local `backend/.venv`; leave the shared environment alone.
- Resolve to the package versions captured in the FEAT-057 pre-run inventory:
  Python 3.12.10, pytest 8.4.2, Ruff 0.16.4, mypy 1.20.2, Pydantic 2.13.4,
  SQLAlchemy 2.0.52, Alembic 1.19.1, plus the newly available Pillow,
  python-multipart, and AV 18.1.0 dependencies. Do not install model/GPU
  extras or weights.
- The first unpinned resolution selected newer Pydantic and caused one mypy
  type-check failure in BE2-12. Reproduce it, align to the recorded versions,
  and rerun the exact component pack. The final pinned pack passes without a
  product-source change.
- Preserve SQL collection-only boundaries and all card approval, acceptance,
  and status records. Offline component PASS is not full-card or runtime PASS.

## X02 BE2-07 invalidation adoption — 2026-10-20

- Source review result: X02 remains `NOT_IMPLEMENTED`. BE2-07 emits
  `KnowledgeSupersededV1`, but the existing `RecordingKnowledgeConsumer` is a
  producer-side fixture without a consumer-held fence; BE2-09 exposes no
  adopted operation that applies the event to the exact dependent review or
  playback target.
- Required owner/card adoption: define exact bundle-to-video lineage and adopt
  an idempotent invalidation receiver or current-eligibility resolver, with the
  BE2-07 validity fence held through review commit and playback dispatch/fetch.
  Specify duplicate, replay, and lost-delivery behavior.
- Evidence: `evidence/notes/CROSS_LANE_X02_REVIEW_20261020.md` and
  `evidence/metrics/CROSS_LANE_X02_20261020.json`. This is a source review, not
  a behavior test. No card contract/status/acceptance or runtime gate changed.

## Owner-directed cross-lane contract direction — 2026-10-21

The owner's direct instruction is recorded verbatim in
evidence/notes/OWNER_DESIGN_DISPOSITION_FOUNDATION_UOW_20261021.md and the
relevant owning-card DECISIONS.md files. The selected direction is: BE2-01 owns
the shared foundation UoW and BE2-08 is a non-committing participant; BE2-07
source fencing is checked/held in the finalizer UoW only for a shared
transactional store; job/run/source-pin mapping comes from persisted foundation
facts while the dispatch envelope stays unchanged; BE2-14 eligibility,
execution and budget remain separate with owner budget inputs pending and
expiry/renewal via a versioned CR; BE2-08 provides a public read-only artifact
model to BE2-09.

New BE2-01 scope draft:
../FEAT-044-be2-ai-job-foundation/plan/CROSS_LANE_FOUNDATION_UOW_SCOPE_DRAFT_20261021.md,
SHA256 B456DEEDF5F892F328E7AEEFF442BC82281400A994EB5A74D791C13856FAB9B0.
It requires review, a frozen minimal manifest and supplemental implementation
approval before source edits. The previous approved card scopes remain unchanged.
Budget unit/limit, reservation timing, exact transaction/recovery details,
same-store fence feasibility, late-result semantics and artifact-read-model fields
remain open as identified in that draft.

X01 remains PARTIAL unless the held same-store fence is implemented and proven.
X05d remains BLOCKED; X05c/CR09-02 remains OPEN; X09-08 remains
NOT_IMPLEMENTED pending persisted-job composition. No card acceptance/status,
runtime gate, source or test changes are inferred or authorized by this decision
record. Modal, Lightning, provider, server, database and runtime remain outside
this offline design update.

## Independent shared-UoW scope review — 2026-10-21

The owner supplied an independent review with verdict CHANGES_REQUIRED. Its findings and exact source snapshot are recorded in evidence/notes/CROSS_LANE_UOW_REVIEW_DISPOSITION_20261021.md and evidence/metrics/CROSS_LANE_UOW_SOURCE_HASHES_20261021.json.

Documentation-only successors:
- FEAT-044 foundation UoW scope revision 2 draft: SHA256 39B0FD5958D2C298460F7605A7F73E8BDC7BC9D269B6399822FD2A2EAAC4DDC4.
- FEAT-057 X01/X05 plan erratum to revision 4: SHA256 7530294B18B30616EB9A968ABF0AD227C661294500CD0789A7EC514D54E5FE39.
- FEAT-050 BE2-08 read-only artifact model supplement: SHA256 F24823A192A90F11649871348AC0C539C3E63501AAA3A75C21DBC36EB7F15FA1.

At the time this review disposition was recorded, owner decision D1 on start/failure lifecycle boundaries remained pending; the later selection A is recorded above and supersedes that state. Current BE2-07 approval cannot supply the same-store held source fence; X01 stays PARTIAL unless a separately approved scope proves it. BE2-08 read-model fields/access/supersession remain pending. X05d remains BLOCKED; X05c/CR09-02 OPEN; X09-08 NOT_IMPLEMENTED until persisted composition is proven. No implementation approval, source/test/approval edit, schema/migration change, card acceptance/status change, or runtime authorization is created by these drafts.

## UoW scope rereview 2 — 2026-10-21

The owner-pasted independent Claude report returned CHANGES_REQUIRED on FEAT-044 scope Rev3. The response is captured in evidence/notes/CROSS_LANE_UOW_CLAUDE_REREVIEW2_DISPOSITION_20261021.md. Current candidates are FEAT-044 scope Rev4 and this feature's plan Rev5, both drafts awaiting Claude rereview. Rev4 and erratum 1 remain immutable history. The D1 selection A remains design direction only; no code approval. X01 PARTIAL, X05d BLOCKED, X05c/CR09-02 OPEN, X09-08 NOT_IMPLEMENTED; budget unit/limit remain unprovided; Modal deferred. No source/test/approval/card status/acceptance change.

## UoW owner decision D2 — 2026-10-21

The owner accepted both recommendations from Claude rereview 2: represent foundation SUCCEEDED/STALE as a distinct terminal BE2-08 video-run state with no artifact/readiness through a versioned CR, and bind VideoRun attempt_id only at S while retry clears the old id and keeps attempt number foundation-owned. Receipt: evidence/notes/CROSS_LANE_UOW_OWNER_DECISION_D2_20261021.md. This does not adopt contracts or approve implementation.
## Seam review authority checkpoint — 2026-10-22

No new owner design decision or implementation approval was inferred from this review. The recorded D3 C1-A/C2-A choices remain design direction only; CR08-01 shared UoW/recovery and the BE2-07 durable source fence remain unadopted gates. The existing FEAT-044 manifest stays limited to typed dispatch routing. FEAT-057 will not substitute a fake admission, UoW, or finalizer for these contracts. See evidence/notes/BE2_01_07_TO_08_SEAM_BLOCKER_20261022.md.

## Persisted VideoWorker seam scope proposal — 2026-10-22

Decision state: proposal prepared for owner review only; no contract adoption, source permission, or approval is inferred. Candidate contract, per-owner paths, acceptance, exclusions and gates are in `plan/BE2_01_07_08_PERSISTED_VIDEO_SEAM_SCOPE_DRAFT_20261022.md`. Preserve the existing envelope. Do not implement while CR08-01, BE2-07 durable fencing, owning-card supplemental approvals, D4 disposition, and the database-test constraint conflict remain unresolved. Do not use a fake BE2 UoW/admission/finalizer to claim completion.

## Owner scope correction and local database test authorization — 2026-10-22

Scope direction: one BE2-07 bundle → BE2-01 persisted job/run and unchanged-envelope dispatch → real BE2-08 VideoWorker and adopted accepted-result receipt flow. The owner allows one dedicated local isolated database with synthetic data for later transaction/persistence verification, after exact scope and card approvals are updated. This does not authorize database provisioning, test runs, source/test edits or schema/migration changes now. Exclude BE2-09, BE2-14, D4 and BE1 implementation. Durable source fencing is a separate gate; X01 stays PARTIAL until held through finalization is proven. Scope Rev2 is only a proposal. CR08-01 and owning-card approvals are not adopted by this decision.

## Owner adoption of BE2-VIDEO-LIFECYCLE/1 — 2026-10-22

The owner adopted A/S/B and identity-failure exactly as §2 of the hash-pinned scope Rev2. BE2-01 owns transaction begin/commit/rollback; BE2-08 participates through the typed transaction-bound contract and writes only its own rows. The three supplemental FEAT-044/050/057 approval records were updated and verified against the exact §4 manifests before source/test edits. PostgreSQL use remains limited to a new, dedicated loopback PG17 database with synthetic data for offline transaction/persistence tests. No database was created because this worktree has no PG17 test endpoint/password-file configuration. This adoption does not close the durable source-fence gate; X01 remains PARTIAL. See `evidence/notes/BE2_01_07_08_PERSISTED_VIDEO_FLOW_IMPLEMENTATION_20261022.md`.
