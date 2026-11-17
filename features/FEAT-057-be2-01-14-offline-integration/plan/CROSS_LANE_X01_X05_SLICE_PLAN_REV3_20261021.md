# BE2 cross-lane X01/X05 vertical-slice plan

- Status: `G0_DIRECTION_FINALIZED_AT_FEAT-057_SCOPE` (card contract adoption and implementation approval pending)
- Revision: 3
- Feature: FEAT-057 offline cross-lane integration
- Candidate observed: `feature/be2-backend-ai-integration` at
  `1649b72978877d82b4d7662040ff3555dee0a3a7`
- Prepared: 2026-10-21 (Asia/Saigon)

This plan selects the first implementation slice after the X01 Modal rerun. This
is a plan review, not implementation approval. It does not amend the approved
FEAT-057 scope, authorize card-owned code or contracts, change card
status/acceptance, or authorize Lightning/runtime work. Implementation starts
only after the owner and affected card owners approve the contracts and
file/scope boundaries below. Existing card approvals, acceptance, and statuses
remain unchanged.

The repository owner's 2026-10-21 disposition is recorded in §4 and
`evidence/notes/OWNER_DISPOSITION_X01_X05_20261021.md`. Agreed design direction
does not itself adopt a card-owned contract or grant implementation approval.
OD-X05c and the Modal environment gate remain open/deferred; OD-X05d is
conditional on an already-adopted current-source resolver/fence.

The independent source-contract review of G0 returned **PASS** for finalizing
this direction at FEAT-057 scope. The PASS confirms the requirements are
consistent with the candidate interfaces when recorded as proposed, adoption-
gated contracts. It does not say those interfaces have durable cross-card
adapters or owner adoption. Specific gaps and owner-confirmation items are
recorded in §4A and
`evidence/notes/G0_CONTRACT_REVIEW_20261021.md`.

## Revision 2 review disposition — 2026-10-21

- R1 — The previous G4 required an invalidation race test at review/playback
  without identifying the unadopted X02 receiver/current-source boundary. This
  revision makes adopted current-source authority a gate and keeps X02
  implementation outside this slice.
- R2 — The previous policy gate was framed as a pre-dispatch check. Current
  ports require BE2-08 phase-specific current policy/kill/budget checks, while
  BE2-14 current-use eligibility alone does not authorize worker/provider
  execution or reserve budget. This revision records those as separate adoption
  requirements for the narrow BE2-08 path.
- R3 — Replaced the relative “tomorrow” test timing with an explicit owner-resume
  gate so this plan does not imply current test authorization.
- R4 — Several frozen card-plan headers still show planning-only states, while
  their later approval/status records supersede those headers. This review uses
  the current approval and status records, leaves all card records untouched,
  and preserves each card's open integration/runtime gates.
- R5 — Clarified that atomic submission and atomic finalization are separate
  foundation-owned commits around external generation, not one transaction
  spanning provider work.

## 1. Recommendation and outcome

Proposed outcome: compose one vertical path from exact BE2-07 knowledge export
→ BE2-01 job and attempt identity → BE2-08 generation and committed output →
BE2-09 explicit review and playback eligibility. The slice targets the missing
commit/fence boundary behind X01 and the real artifact required by X05; neither
is complete until owner adoption and the scoped evidence pass.

Include the **BE2-08-only subset of X09**. Source review shows that the
foundation `DispatchWorker` currently invokes its `AiProviderPort` directly,
while BE2-08's `VideoWorker` is a separate entrypoint accepting the same
dispatch envelope; no adopter routes a foundation job to that video worker.
Without this minimal typed route, the proposed path could create a job and call
BE2-08 directly, but could not claim the foundation job was actually dispatched
to BE2-08. Keep BE2-13 routing out of this slice. If the route contract is not
adopted, stop before claiming X09-08 or a complete foundation-to-video path.

## 2. Verified baseline and evidence boundary

- X01 is `PARTIAL`: the real BE2-07 exact export reaches the real BE2-08 media
  preparation pipeline, and stale-source cases are rejected before promotion.
  There is no foundation job submission, committed BE2-08 run/artifact, or
  producer-validity fence held through that commit.
- X02–X09 are `NOT_IMPLEMENTED` in the current integration evidence.
- The owner-provided Modal run passed 296/296 tests on the SHA-pinned source ZIP
  (`5e7d3e10c8ef5439efc6a39dd6a17774ec40e746b054153b004215f6479ca9e8`). It
  covers X01 plus adjacent BE2-07/08 offline regression only; it does not
  establish the missing job/artifact commit, a live queue/worker, Lightning,
  provider, database, or full BE2-01–14 integration.
- Preserve the current dirty worktree and receipts. Do not reset, clean, stage,
  commit, or publish as part of this plan.

Source evidence: `evidence/notes/CROSS_LANE_X01_REVIEW_20261020.md`,
`evidence/notes/CROSS_LANE_X01_MODAL_RUN_20261020.md`, and
`evidence/metrics/CROSS_LANE_X01_MODAL_20261020.json`.

## 3. Source-traced contract and ownership review

| Owner/card | Current public candidate surface | Adoption status and consequence |
|---|---|---|
| BE2-07 — FEAT-056 | `KnowledgeBundleService.resolve_exact` (`backend/src/sketch2life/application/services/knowledge_bundle.py:586`); FEAT-057 adapter `KnowledgeScriptVideoSourceResolver` (`backend/src/sketch2life/infrastructure/cross_lane/knowledge_script_video.py:21`). | Offline component acceptance is recorded in `features/FEAT-056-be2-knowledge-script/approvals/COMPONENT_ACCEPTANCE.md`; it accepts only that component and leaves the card `IN_PROGRESS / NOT_DONE`, actual BE2-08 adoption/lease/fence, and cross-card integration open. The resolver proves exact read and source pin, not a fence held through final commit. The frozen plan header still shows a planning-only state; later acceptance/status records govern. |
| BE2-01 — FEAT-044 | `AiJobService.create_job` (`backend/src/sketch2life/application/services/ai_jobs.py:337`); `DispatchWorker.handle` (`backend/src/sketch2life/infrastructure/ai_jobs/worker.py:56`). | Phase B B1–B6 is separately approved in `features/FEAT-044-be2-ai-job-foundation/approvals/PHASE_B_TASK_APPROVAL.md`; BE2-01 remains `IN_PROGRESS`, with A17 Studio as a separate runtime gate. The approval does not itself adopt BE2-08 routing, the BE2-07 source fence, or BE2-09 review/session access. The Phase B plan header still says `AWAITING_APPROVAL`; the later approval record governs. |
| BE2-08 — FEAT-050 | `VideoCreateService.create` (`backend/src/sketch2life/application/knowledge_video_create.py:88`) uses `AtomicVideoSubmission` (`backend/src/sketch2life/application/ports/knowledge_video.py:89`); `PreparedVideoMedia` is explicitly uncommitted (`backend/src/sketch2life/application/knowledge_video_media.py:74`); `AtomicVideoFinalizer` (`backend/src/sketch2life/application/ports/knowledge_video_worker.py:91`) requires an adopted foundation UoW. | The task approval in `features/FEAT-050-be2-knowledge-video/approvals/TASK_APPROVAL.md` covers card-local P1–P4/P5 preparation, not cross-card adoption. BE2-08 remains `IN_PROGRESS`; CR08-01 is open and no runtime adapter supplies atomic submission/finalization. Its frozen plan header still says `AWAITING_APPROVAL / NOT_STARTED`; the current approval and status records govern. Sequential commits cannot be described as atomic. |
| BE2-09 — FEAT-051 | `ReviewWriteAccess.resolve` and `ReviewWriteBoundary.guard` (`backend/src/sketch2life/application/ports/video_review_write.py:95,123`) require exact current artifact/authority and held owner fences. | BE2-09 remains `IN_PROGRESS`; its task approval is card-local. CR09-01 (canonical review head/combined DATA-27 projection) and CR09-02 (BE1 session/access receipt and each-use gateway) remain open in `features/FEAT-051-be2-video-review-playback/DECISIONS.md`. Its frozen plan header still says `AWAITING_APPROVAL / NOT_STARTED`; the current approval/status records govern. Do not rewrite BE2-08 rows or migrations; until adoption, do not claim integrated playback or actual `playing`. |
| BE2-14 — FEAT-049 AI policy | `PolicyUseBoundary` / `PolicyUseAccess.decide_use` (`backend/src/sketch2life/application/ports/ai_policy_use.py:15-44`); BE2-08 `RenderAuthority.check` (`backend/src/sketch2life/application/ports/knowledge_video_media.py:94-100`) and its phase checks (`backend/src/sketch2life/application/knowledge_video_media.py:125-182`; `backend/src/sketch2life/application/knowledge_video_worker.py:192-238`). | BE2-14 remains `IN_PROGRESS`; current owner/provider integration is open. No adopted BE2-08 policy binding/fence exists. BE2-08 requires current policy/profile epoch, kill, and budget gates at its applicable phases and finalization. BE2-14 current-use eligibility alone does not grant worker/provider execution or reserve/account for budget. Adopt the exact narrow BE2-08 policy, execution, and budget boundaries before enabling this slice; broader X08 consumers remain out of scope. Its frozen plan header still says `AWAITING_APPROVAL / NOT_STARTED`; the current approval/status records govern. |

### X09-08 dependency finding

`DispatchWorker` (`backend/src/sketch2life/infrastructure/ai_jobs/worker.py:51-78`)
calls the foundation provider port and has a singleton installation hook. BE2-08
has its own `VideoWorker.handle` (`backend/src/sketch2life/application/knowledge_video_worker.py:279-292`)
which validates a `WorkerDispatchEnvelope` against a configured video job type.
The reviewed tree contains no typed registration/adopter from the foundation
dispatch to this BE2-08 worker. Therefore X09-08 is **required** for the proposed
real dispatch path. This plan includes that narrow route only; X09-13 and the
remaining X09 consumers stay out of scope.

## 4. Owner disposition and card-owner adoption gates

The following dispositions are the repository owner's direction for FEAT-057's
plan. “Agreed” means the proposed requirement/design is accepted as the
integration direction; it does not assert that an affected card owner has
adopted it or approved implementation.

| ID | Owner disposition | Remaining card-owner adoption / stop condition |
|---|---|---|
| OD-X01 | **Agreed.** Require exact source identity and a validity fence effective through BE2-08 finalization. | BE2-07/08 owners must adopt the protocol. Post-read checks alone do not protect commit; keep X01 `PARTIAL` until the boundary is demonstrated. |
| OD-X05a | **Agreed.** Use two separate foundation-owned atomic boundaries: `AtomicVideoSubmission` commits run + foundation job + dispatch/receipts; `AtomicVideoFinalizer` commits completion/artifact/receipt/outbox with run/job CAS, current fences, and recovery semantics. | BE2-01/08 owners must adopt both boundaries. Provider generation occurs between them; do not claim one transaction spans provider work. Sequential commits within either boundary are prohibited. Foundation UoW/schema/migrations require their owning plan and approval. |
| OD-X05b | **Agreed.** Resolve CR09-01 with a canonical review head and combined DATA-27 projection against the exact BE2-08 artifact, without rewriting BE2-08 rows/migrations. | BE2-09 owner must record contract adoption. Until then, the candidate review port is not integrated behavior. |
| OD-X05c | **Open.** No disposition to close CR09-02 yet. | BE1/BE2-09 owners must resolve actual session/access receipt and each-use gateway. Until then, offline review/playback-intent evidence cannot claim an actual session start or playable access. |
| OD-X05d | **Agreed conditionally.** Use only a current-source resolver/fence already adopted by its owner; if none is available, X05 remains incomplete and X02 is not pulled into this slice. | BE2-07/09 owners must identify the adopted resolver/fence. Any new `KnowledgeSupersededV1` receiver/event binding or BE2-09 contract change requires a separate X02 owner decision and approval. |
| OD-X09-08 | **Agreed.** Include only the typed route from the foundation dispatch envelope/job type to `VideoWorker`, preserving job, attempt, subject/session, source pin, and idempotency. | BE2-01/08 owners must adopt the route. Do not include BE2-13 routing. |
| OD-POLICY-08 | **Agreed.** Require narrow, phase-specific BE2-08 policy/disable/kill-generation checks and separately identify worker/provider execution authorization and budget/concurrency reservation/accounting boundaries. | BE2-14/08 owners must adopt and wire applicable checks fail-closed. A pre-dispatch snapshot or BE2-14 current-use eligibility alone is insufficient. No dispatch, generation, or finalization before adoption; broader X08 consumers stay out of scope. |
| OD-ENV | **Deferred.** Modal CPU with pinned source archive and no secrets remains the proposed reproducibility check. | Test execution waits for a separate explicit owner resume instruction; this plan does not authorize or run it. |

Affected card owners must record their contract and implementation approval in
their owning feature records. FEAT-057 approval alone does not grant those
changes.

## 4A. G0 source review classification

This classification separates current candidate behavior from the direction
selected for FEAT-057. “Existing candidate” means a source interface or
component behavior was found in this worktree; it does not mean a durable
cross-card adapter, role-owner adoption, or production authority exists.

| Direction | Existing candidate evidence | FEAT-057 direction and remaining confirmation |
|---|---|---|
| X01 exact source and fence | BE2-07 `resolve_exact` checks a requested bundle ID/version/hash and its current resolution; the FEAT-057 adapter also compares organization, session, editorial/context/audience revisions, source refs and hashes. Those reads finish before BE2-08 finalization. BE2-07 acceptance explicitly leaves actual BE2-08 adoption/lease/fence open. | Preserve the exact source identity, including bundle/version/hash and audience/context identity, and hold or atomically validate the adopted validity fence through finalization. BE2-07/08 owners must define and adopt fence owner, scope, linearization and lifetime. A post-read check is insufficient; X01 remains `PARTIAL` until demonstrated. |
| X05a submission and finalization | Candidate `AtomicVideoSubmission` documents one commit for run, foundation job, dispatch and semantic/receipt/audit records. Candidate `AtomicVideoFinalizer` documents one authorized foundation UoW with run/job CAS, current fences, exact receipt/audit/outbox, and recovery lookup. BE2-08 status says durable adapters and the actual CR08-01 bridge are open. | Keep two separate commits: submission (run + foundation job + dispatch/receipt) and finalization (completion + exact artifact + receipt/outbox with job/run CAS, fences and recovery). Provider generation sits between them. BE2-01/08 must adopt the exact enlisted records, transaction authority, rollback/recovery and receipt ownership; no transaction crosses provider work. |
| Replay, races and late results | Candidate submission docs define body-bound receipt replay and authorization before semantic deduplication. Worker recovery distinguishes known-absent finalizer lookup from unavailable lookup; ambiguous finish returns pending rather than rerendering. The finalizer candidate requires current-attempt validation, CAS and held fences. No durable cross-card implementation or adopted race contract was found. | Require retries/lost acknowledgements to return the same authoritative operation/receipt identity without another job, run or artifact. A late result may commit only if its attempt still wins the adopted CAS and current source/policy fences remain valid through commit. BE2-01/08 must confirm receipt scope, duplicate winner, late-attempt arbitration and replay authorization semantics; these are required decisions, not demonstrated behavior. |
| X09-08 typed route | Foundation `DispatchWorker` calls its provider directly; BE2-08 `VideoWorker` accepts the foundation envelope and rejects a mismatched configured job type. No foundation-to-VideoWorker binding exists. The current envelope carries message/job/attempt/type/request reference and capability, but no explicit source pin or idempotency key. | Add only a typed BE2-08 route, with unknown types failing closed. BE2-01/08 must define how subject/session, source pin and idempotency are resolved from the immutable foundation job/run or carried by an adopted versioned contract; do not infer that they are already in the envelope. Keep BE2-13 out. |
| X05b / CR09-01 | BE2-09 has candidate guarded review-write/head storage. Its dependency register still marks canonical review-head and combined DATA-27 projection adoption open; exact artifact hash/version is distinct from source-pin digest. | Require the canonical review head/projection to bind the exact BE2-08 artifact hash/version. BE2-09 adoption is required. Do not write BE2-08 rows or migrations. |
| X05d current source | Exact BE2-07 resolution and a FEAT-057 process-local fixture coordinator exist. Neither is an owner-adopted resolver/fence held through BE2-09 use/finalization. | Conditional only: consume a current-source resolver/fence already adopted by its owner. None is established in the reviewed record, so X05 stays incomplete. Do not add an X02 receiver/event in this slice. |
| POLICY-08 | BE2-08 candidate `RenderAuthority` has phase checks around prepare, source resolution, generation, validation, staging and finalization. BE2-14 has current-use eligibility and guarded accounting components, but current status says real owner/provider bindings, worker authorization and atomic budget/concurrency adoption are open. | Adopt fail-closed, phase-specific BE2-08 policy/disable/kill-generation checks through finalization. Keep current-use eligibility separate from worker/provider execution authorization and from budget/concurrency reservation/accounting. BE2-14 eligibility alone grants neither execution nor budget. |
| X05c / CR09-02 | BE2-09 candidate playback intent/receipt is historical evidence; its status and dependency register leave actual BE1 session/access receipt and each-use gateway open. | Keep open. No actual session start, current access or playable media claim follows from review/playback intent. BE1/BE2-09 adoption and conformance remain required. |
| OD-ENV | Prior evidence is a scoped offline test run; no current execution authorization follows from it. | Modal remains deferred until a separate explicit resume instruction. |

The unresolved items above block card-owner adoption and implementation, not the
FEAT-057 direction review. Keep X01 `PARTIAL` and X02–X09
`NOT_IMPLEMENTED`; keep every card's status and acceptance unchanged.

## 5. Execution steps and gates

### G0 — Direction finalized; adoption gate remains open

The independent source review and repository-owner direction decision are
complete at FEAT-057 scope. The reviewed field map and current-versus-required
contract classification are in §3 and §4A. Before implementation, refresh the
source snapshot and obtain the affected card-owner adoption and implementation
approvals for the unresolved items recorded there.

1. Preserve the candidate tree and pin its commit and source hashes. Recheck
   candidate and remote refs before any implementation worktree/branch or
   publication operation.
2. Refresh the plans, approvals, status, public ports and handoffs for
   BE2-01, 07, 08, 09 and—if applicable—14 before relying on this review.
3. Confirm the field-level map: job ID/type, attempt ID, subject/session, exact
   BE2-07 bundle/version/hash/audience, current-source authority/fence,
   BE2-08 run ID, artifact reference/hash, idempotency key, and
   invalidation/policy generation. Keep current-source authority distinct from
   X02 invalidation delivery.
4. Obtain owner confirmation of transaction and receipt scope, fence owner and
   lifetime, replay/duplicate/late-result semantics, the typed-route source
   mapping, and the exact BE2-09 consumer query. Record any unavailable contract
   as a blocker; do not infer it from a fixture or post-read check.

The current `WorkerDispatchEnvelope` is not itself the source-pin or
idempotency carrier. The adopted route must specify the authoritative mapping
from the foundation job/request and BE2-08 run to those values, including
subject/session identity, or define a versioned envelope change through the
owning card records. Do not fill this gap by inference.

**Gate:** FEAT-057 direction is finalized, but affected card owners must record
contract adoption, per-card scope, evidence location and implementation
approval in their own records. FEAT-057 approval does not substitute for those
approvals. No code or test execution for this slice before that gate.

### G1 — Pre-dispatch owner and policy gates

1. Confirm the approved BE2-01 foundation surface and the distinct
   BE2-07/08/09 owner-fence protocols; Phase B approval is not cross-card
   adoption.
2. Resolve OD-POLICY-08 before job creation or dispatch. One pre-dispatch
   snapshot is insufficient: adoption must cover the applicable BE2-08 worker
   phase checks and finalization, and separately establish execution and budget
   authority. If those gates are not adopted, leave job creation/dispatch
   unperformed.
3. Confirm OD-X05d current-source authority for BE2-09. If it needs an X02
   receiver or contract change, stop and leave X02 outside this implementation.
4. Confirm CR08-01 and CR09-01/02 owners and exact allowed change locations.

**Gate:** all required public ports and owner approvals exist. No code or test
execution before this gate; missing gates remain named blockers.

### G2 — Foundation job routing to BE2-08 (X09-08 subset)

1. Add only the adopted typed handler binding from the actual foundation
   dispatch envelope/job type into BE2-08 `VideoWorker`.
2. Preserve job type, job/attempt ID, subject/session, idempotency, and exact
   BE2-07 source pin through dispatch using the mapping adopted at G0. Unknown
   types fail closed without calling a video/provider handler.
3. Prove duplicate dispatch remains within the foundation attempt/recovery
   rules; do not register BE2-13 or claim a general shared registry.

**Gate:** a foundation-created job reaches BE2-08 through the adopted route and
the worker receives the unchanged producer-created source pin.

### G3 — BE2-08 output finalization and X01 fence

1. Run the actual BE2-08 application pipeline using deterministic external
   generator/decoder fakes only. Preserve the adopted phase checks at each
   applicable `RenderAuthority` point; a pre-dispatch policy snapshot is not a
   substitute.
2. Finalize completion through the adopted `AtomicVideoFinalizer` foundation
   UoW. Link one foundation job/attempt, one BE2-08 run, one exact artifact
   reference/hash, and its receipt/outbox to the BE2-07 source identity. If the
   existing public port cannot express the approved protocol, stop for a
   card-owned plan/contract revision; do not implement an inferred substitute.
3. Hold or atomically revalidate the BE2-07 validity fence through the
   finalization boundary. Enforce the adopted BE2-14 current policy/kill/budget
   gates at the applicable worker phases and finalization; current-use
   eligibility alone does not authorize worker/provider execution. Invalidation,
   audience change, policy-generation stop, or stale source before commit must
   leave no accepted artifact/completion.
4. Prove receipt lookup/replay, lost acknowledgement, duplicate completion,
   and late result handling. Do not introduce shared database or migration
   changes without a separate approval.

**Gate:** the committed output is producer/consumer-service-created, exact,
idempotent, and cannot be promoted after source invalidation or policy stop. If
the only proof is a process-local fake coordinator, report that evidence as
offline protocol simulation and keep runtime/durable-fence adoption open.

### G4 — BE2-09 review and playback eligibility (X05)

1. Resolve the finalized artifact through BE2-09's adopted `ReviewWriteAccess`
   contract, CR09-01 canonical head/projection, and the adopted current-source
   authority in OD-X05d; carry exact source, artifact hash/version, audience,
   policy and review revision.
2. Require explicit review against that identity. Wrong hash, stale/revoked
   source, changed audience, non-approved moderation, or non-approved review
   fails closed.
3. Test current authorization for a playback intent only if CR09-02's public
   seam is adopted. Until actual BE1 receipt/gateway wiring is separately
   adopted and proven, report actual session start/access as `NOT_RUN`, not
   `playing`.
4. Do not implement BE2-07 invalidation delivery/receiver in this slice. If
   review/playback cannot use an already adopted current-source resolver and
   held fence, leave X02 `NOT_IMPLEMENTED` and keep X05 `NOT_IMPLEMENTED` (or
   `PARTIAL` only for behavior actually demonstrated); request a separate X02
   owner decision for any new event receiver or contract.

**Gate:** BE2-09 consumes committed lineage through CR09-01 and an adopted
current-source boundary. Offline review and playback-intent eligibility alone
leave X05 `PARTIAL`; if current-source authority needs X02 event delivery, that
remains a separate blocker and scope. Full X05 PASS also needs the CR09-02
current session/access receipt and gateway contract adopted and exercised. Until
then, actual session start/access stays `NOT_RUN`; do not infer `playing` from an
accepted intent or a Modal result.

### G5 — Review and scoped offline verification (deferred)

1. When the owner resumes testing, run new X01/X05/X09-08 tests, the existing
   cross-lane registry tests, and directly
   affected BE2-07/08/09 component regressions on one pinned snapshot.
2. Run Ruff, strict mypy, harness, repository-security, architecture,
   skeleton, and `git diff --check`; retain command, exit, JUnit, and source
   hashes in FEAT-057 evidence.
3. Obtain review from the affected card owners. Update the edge registry only
   from the tests and contract adoption actually demonstrated.
4. Build a new source ZIP from the final reviewed snapshot and run the agreed
   offline suite on Modal CPU when the owner asks to resume testing. Download
   and hash the run receipt, JUnit, and log before stopping the notebook kernel.

**Gate:** X01/X05 are `PASS` only if their adopted contracts and full offline
edge criteria pass. X09-08 is a separately reported subset and does not close
X09-13. Any missing adoption stays `NOT_IMPLEMENTED`; skipped/unavailable
checks stay `NOT_RUN`. Lightning, provider, DB and real session/access runtime
remain separate gates.

## 6. Acceptance for this slice

- **A1:** source ZIP/tree, branch commit, and executed test source hashes match.
- **A2:** all job, attempt, run, artifact, and source identifiers match across
  producer, worker, finalizer, and review consumer.
- **A3:** stale/revoked source or a policy-generation stop before finalization
  leaves no accepted artifact/completion. Current-source behavior at BE2-09 is
  gated separately under OD-X05d; no X02 implementation is implied.
- **A4:** duplicate delivery, replay, lost ACK, and late completion do not
  create a second run/artifact or overwrite a winning terminal state.
- **A5:** BE2-09 requires explicit review and current source/authorization for
  playback intent of the exact committed artifact; if OD-X05d is not adopted,
  X05 remains incomplete. Actual session/access is not claimed without CR09-02.
- **A6:** all required focused tests and validators pass; phase-specific policy,
  execution, budget, current-source, and residual owner/runtime gates are
  explicit. Fake-only checks do not prove adoption.
- **A7:** X09-08 is reported independently from X09-13; it cannot imply the
  whole X09 edge passed.
- **A8:** BE2 card approvals/statuses remain unchanged; FEAT-057 reports only
  integration evidence, not full-card acceptance or runtime readiness.

## 7. Modal versus Lightning

Modal is suitable for the scoped offline Python suite: upload the `.ipynb` and
the source archive, run CPU-only with pinned dependencies and deterministic
external fakes, then preserve the receipt/JUnit/log. Modal's hosted notebook
documentation describes cloud notebook execution, configurable CPU/memory/GPU,
and an ephemeral filesystem unless a Volume is attached:
https://modal.com/docs/guide/notebooks.

The prior owner instruction deferred execution and identified Modal as the
planned host for a later offline rerun. That deferral is not current execution
authority: this plan does not authorize or run tests. Resume only after a
separate explicit owner instruction.

This does **not** replace Lightning/Studio acceptance. Lightning AI Studio is a
separate persistent cloud workspace intended for development and AI/ML
workloads: https://lightning.ai/docs/overview/ai-studio/. Modal CPU evidence
cannot establish the approved BE2-01 A17 Studio checkpoint, live workers,
provider/model behavior, GPU/decoder execution, database integration, or any
per-card runtime gate. Keep those as `NOT_RUN` until the correct runtime is
available and the owning card's approval authorizes the exact entrypoint.

