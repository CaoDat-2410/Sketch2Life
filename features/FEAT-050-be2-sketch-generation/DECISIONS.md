# Feature decisions

## 2026-10-18 — owner approval of SK1 (plan revision 5)

- Owner approved SKETCH_COMPONENT_OFFLINE on plan revision 5 (SHA256 461d0684…) with Q1–Q6 as
  recommended; verbatim in `approvals/TASK_APPROVAL.md`. Offline component scope only.
- Feature number FEAT-050 chosen as the next unused number in the local inventory (both this
  line and the second executor's local snapshot end at FEAT-049). A future collision with the
  second executor's numbering is recorded as a join-time item; nothing is renamed now.

## Technical choices TC-01–TC-25 (plan revision 5 §11)

Adopted as written in plan §11 for this component, with these clarifications:

- TC-21 / TC-25 (actor set): every path that changes artifact quarantine state in the chain
  goes through the single `CoordinatedSketchArtifactPort` instance — (1) the A1-facing
  `AiJobService` (completion side effects and shared-outbox drain), (2) the sketch
  `AiJobService` (same), (3) C9 `deliver_cleanup`, (4) the test owner hook
  `owner_quarantine`. The raw `FakeArtifacts` is used only for `put` and read-only assertions.
  The "three actors" wording left in plan TC-21 is superseded by plan §6.3 (four actors).
- R31 with an UNSAFE fixture keeps `blocked_unsafe` (plan §5.2); the pending → stale after
  quarantine assertion uses a validly promoted fixture (as R25). No new transition is added.
- The chain builder constructs `CanvasFacts` directly instead of importing the private A1
  helper `_canvas`.

## 2026-10-18 — SK1 implementation checkpoint (not owner acceptance)

- Implemented the approved offline component in this branch. Focused suite: 147 passed; BE2-01,
  BE2-02 and BE2-03 regression suites: 875 passed, 3 skipped. Strict mypy passed on all 14 new
  Python files. The final Ruff rerun and Claude's independent review remain pending.
- No SQL/Redis, real provider, decoder, Studio, or durable multi-process behavior was exercised.
  SK1 and the full BE2-04 card remain unaccepted / NOT_DONE pending review and later gates.
- During verification, `uv` temporarily created `backend/.venv`, `backend/uv.lock`, and a local
  package cache despite the approved no-dependency-install boundary. Those artifacts were
  removed; no dependency manifest or lockfile change remains. Full details are in the SK1
  implementation evidence note and ignored local handoff.

## 2026-10-18 — Codex response to independent SK1 review (pending re-review)

- F-1: `schedule()` only writes the proposal when cleanup-job identity actually changes. A no-op
  cleanup CAS must not increment/compare the proposal revision; the worker-link/cancel race has a
  regression.
- F-2: non-Teacher READ returns `RESOURCE_NOT_FOUND` before checking proposal existence. Existing
  and missing IDs therefore have the same response; non-Teacher cancellation rules are unchanged.
- F-4: owner notice first commits stale/invalidation state, then best-effort cancels the recorded
  active job outside the unit of work.
- F-5: the SK1 chain routes shared-job eligibility by `job_type`, so retries for Sketch use
  `SketchEligibility`; Vision still uses A1 `AssistanceEligibility`.
- **Pending owner disposition — approved-plan deviation:** plan §6.5 says the rebuilt A1
  composition may differ only by the shared coordinated artifact port. The implementation also
  wraps the A1-facing eligibility with `SketchChainEligibility` so a shared retry sweep applies
  `SketchEligibility` to Sketch jobs and preserves A1 eligibility for Vision. This fixture-only
  deviation closes the reviewed stale-Sketch redispatch defect; it does not modify the A1 builder
  or approved plan bytes. SK-C11 covers the selected A1 parity cases, but owner disposition is
  required before SK1 closure.
- F-6: replaying `open_from_handoff` for a REQUESTED proposal with no linked job retries scheduling.
  This is caller-driven recovery only; it does not claim a durable background retry.
- The second follow-up corrected R03's post-dispatch assertion and evidence, added the R11 link,
  stage, cancel and notice commit-failure matrix, chain coverage for P08/P11 and N23, a registry-
  sourced C05 report, and precise source-hash/epoch assertions for P01/N18. Owner-notice cleanup
  also propagates the concrete status reason to the foundation cancellation command.
- Claude must re-review the new tests and evidence. R31/R33 remain partial because their injected
  intents are synthetic; additional chain/contract mapping and the A1 callback remain untested.
- Coverage added for P07, R12, N13 timeout exhaustion, N12 and N18 chain behavior, SK-C10 teardown,
  and the concrete R06/R31/R32/R33 paths. Remaining partial acceptance is listed in
  `evidence/notes/SK1_CODEX_FOLLOWUP_20261018.md`. No owner acceptance is inferred.

## 2026-10-18 — Claude follow-up 3 (pending Codex review)

- P3: when a created job loses its link to an invalidation, `schedule()` cancels the orphan with
  the status reason of the proposal version it was created for; `SCHEDULE_REFUSED` is the fallback
  (schedule refused, or no terminal reason). Teacher cancellation and owner-notice cleanup keep
  their existing reasons. Regressions cover consent, Teacher cancel and the refused path.
- R31/R33 now also run with quarantine intents generated by real UNSAFE completions (Sketch, and
  Vision for R33); the synthetic-intent tests remain as additional coverage.
- C06: the H-AI-REVIEW example bundle is produced by `build_sketch_examples()` and compared for
  exact equality; the earlier hand-written example is superseded (its inconsistent values are
  noted in the follow-up evidence).
- Not changed: F-5 deviation (owner disposition pending); A1 callback end-to-end stays NOT_RUN
  pending disposition; N16 behaviour stays as planned pending owner acknowledgement; partial
  mapping rows (N04/N08/N11 chain, C03/C03b contract column) stay partial.

## 2026-10-18 — Codex focused review of Claude follow-up 3

- Review verdict NEEDS_CHANGES: one P2 verification finding at the new real-intent R31 test,
  plus two P3 evidence wording notes. Current coordinated production code is not shown broken.
- A process-local no-coordinator mutation passes the current R31 assertions even when raw
  quarantine precedes C8 state publication; the before-commit marker is insufficient proof.
  R31's completion provenance passes, while its lock/order claim remains partial pending a
  stronger handshake/assertion. Keep the original evidence and record this correction separately.
- P3 schedule-reason fix, R33 completion-intent draining, P02/P06 and producer-built C06 pass
  review. Independent focused175/0skip, Ruff and strict mypy pass; X01–X03 receipts were audited.
- No owner disposition/acceptance is inferred; pending F-5 and other residuals remain open.
  Source/tests/fixtures/approval/approved plan were not edited. Evidence:
  `evidence/notes/SK1_CODEX_FOLLOWUP3_REVIEW_20261018.md`.

## 2026-10-18 — Claude follow-up 3a (pending Codex review)

- R31 evidence rests on a held-commit handshake: the C8 unit stays open until the worker reaches
  the coordinated publication, and the raw artifact mutation must observe the committed C8 state.
  A before-commit marker alone is not accepted as proof of post-commit ordering.
- C06 is recorded as JSON value equality (not byte equality); P09 device-view coverage is recorded
  as sampled states plus separately cited tests. No production behaviour changed.

## 2026-10-18 - Codex focused follow-up 3A re-review (not owner acceptance)

- PASS for this delta: F3-R31 and N1/N2 closed. The new raw-mutation observation proves the
  actual committed C8 state; both process-local no-coordinator probes now fail the test as required.
  Independent focused175/0skip, Ruff and strict mypy pass. Production source is unchanged.
- F-5 composition deviation, partial coverage rows, A1 callback NOT_RUN and N16 acknowledgement
  remain owner decisions. SK1 NOT_ACCEPTED; no branch creation or Git publication authorized here.
- Historical review metrics contain CRLF and their exact bytes are now pinned by follow-up 3A.
  Preserve those bytes; include exact-path Git attributes and staged-blob hash verification in the
  later publication plan. The old receipt and Git attributes are unchanged by this review.
- Evidence: `evidence/notes/SK1_CODEX_FOLLOWUP3A_REVIEW_20261018.md` and matching review metrics.

## 2026-10-18 23:15 — owner acceptance of SK1 (offline component)

- Owner (Person 2) accepted SKETCH_COMPONENT_OFFLINE on the snapshot matching
  `evidence/notes/SK1_CODEX_FOLLOWUP3A_REVIEW_20261018.md`; verbatim and snapshot hashes in
  `approvals/SK1_COMPONENT_ACCEPTANCE.md`.
- F-5: `SketchChainEligibility` accepted for the SK1 fixture composition only; not a production
  architecture decision and no change to foundation/A1.
- N04/N08/N11 (chain) and C03/C03b (contract column) stay PARTIAL; the missing parts must be shown
  before claiming the corresponding integration. A1 callback end to end stays NOT_RUN as a test gate
  of a future integration checkpoint (not approved here). N16 accepted as a fixture residual, not a
  public API decision.
- Not full-card acceptance; no runtime claim; stage/commit/push/merge/deploy and branch creation
  need separate instructions. The shared branch `feature/be2-01-07` is to be cut from the accepted,
  committed SK1 tip later.

## 2026-10-19 00:15 +07:00 — shared BE2-01–07 working branch (owner direction, Person 2)

- Workflow: `feature/be2-01-07` is the shared working branch for the sender lane BE2-01–07, created
  from the accepted, committed and pushed SK1 tip `6ab7abf1c52d4e263448fc50236b461f6b5db6c4`. It already contains the
  BE2-01–04 history; nothing was merged or cherry-picked again. The older card branches
  (`feature/be2-01-ai-job-foundation` 6dcc57e, `feature/be2-02-vision-correction` f120c4f,
  `feature/be2-03-assistance-orchestration` 113cdf9, `feature/be2-04-sketch-generation` 6ab7abf)
  remain as historical milestones. The 02-04 milestone branches are not updated; 01 may receive
  reviewed successor fixes through the A17 track described below.
- Next work and fixes for BE2-02–07 happen on the shared branch, each change in its owning
  feature. WIP1: one card in active code scope; every card keeps its own plan, approval, evidence,
  review, component acceptance and commit group.
- BE2-01 fixes follow the A17 track (`feature/be2-01-ai-job-foundation`); a reviewed successor is
  received into the shared branch by pinned SHA with new regression receipts. The A17 package and
  its historical receipts stay frozen; newer source does not inherit the old runtime claim.
- SK1 is accepted offline only; no card becomes DONE through this decision. No next ACTIVE card is
  chosen, no new FEAT number is allocated, and no integration/composition checkpoint is approved.
- Basis: consolidation proposal Rev3 (FEAT-049 ignored local planning, SHA256 e02ffafb…; Codex
  PLAN_REVIEW_PASS, SHA256 4eabc970…) and the SK1 acceptance/publication records.

## 2026-10-19 - Shared-branch routing publication (owner instruction to Codex)

- Direct user instruction: "Bạn làm lun sau đó viết bản cập nhật bàn giao lại cho claude bạn đã làm gì đc k ?"
- Context of that instruction: publish the six pending routing documents as one documentation
  commit on `feature/be2-01-07`, push that branch with upstream, then write a local Claude handover.
  This is separate authorization from the earlier branch-creation instruction; it does not
  change the original SK1 task approval or acceptance bytes.
- Scope: PROJECT_CONTEXT, SOURCE_REGISTER, BE2_EXECUTION_TRACKER, and FEAT-050 CONTEXT,
  DECISIONS and STATUS only. No source/test changes, new ACTIVE card, FEAT allocation, merge,
  integration checkpoint or runtime execution is included. WIP1 and the A17 boundaries stand.
- Baseline: `6ab7abf1c52d4e263448fc50236b461f6b5db6c4`. Verify the exact staged list and pinned
  snapshot; run repository security immediately before commit and again immediately before push.
  Use a normal push; preserve any unexpected remote work.
- Execution results and final tip belong to ignored
  `evidence/local/shared-routing-publication-20261019/receipt.json`; the Claude update belongs
  to `evidence/local/handover/CODEX_SHARED_ROUTING_PUBLICATION_UPDATE_20261019.md`.
