# BE2 AI/job foundation context

- Status: IN_PROGRESS; BE2-01 Phase A (A1–A9) implemented with fakes; approval APPROVED for Phase A revision 1 only (2026-10-14).
- Date: 2026-10-14, Asia/Saigon.
- Owner: P3 / BE2; actual team member unspecified.
- Branch: `feature/be2-01-ai-job-foundation`.
- Baseline: `b9204d8c9eb4f8a1ee6d4db4de5ee23672e0392c`.
- Direct request: “Lên kế hoạch làm Be2 cho tôi đi từ nhánh feature/be2-01-ai-job-foundation này đã có liệt kê task cụ thể r đó và sẽ cần làm gì ?”
- Goal: delivery order for all 14 BE2 cards and a reviewable BE2-01 plan.
- Current change scope: documentation and read-only audit. Proposed code scope: Phase A in `plan/PLAN.md`.
- Non-goals: runtime changes, dependency installation, provider calls, stack adoption, commit/push/deploy.
- Dependencies: SRS v3.1, FEAT-040, ADR-0014/0015 and governance. Phase A needs no live service; Phase B needs separate runtime/persistence decisions and approval.
- Risks: legacy code differs from v3.1; fake storage/copy receipts can be confused with durable recovery/actual deletion; unadopted schemas/numeric policies need explicit labels.

## Context snapshot

Source IDs from `docs/context/SOURCE_REGISTER.md`: `collaborative-srs-v3-20261010`, `four-person-task-backlog-v1`, `owner-four-person-allocation-20261010`, `owner-foundation-answers-20261010`. Canonical SRS v3.1 and ADR-0015 govern this plan; conflicting historical Parent/payment/under-9 scope is not carried forward.

Current target: one-school pilot; Teacher-managed profiles, age 36–155 completed months; one class/40 children capacity target; session/artwork retention 90 days after end. Other data policies and measured capacity remain separate. FastAPI, React Native and Android are confirmed; other runtime/model/storage/queue choices retain ADR gates.

P3 owns AI/content/media domain, adapters, workers, component tests and durable AI jobs. P2 owns identity/class/consent/session/canvas, generic artifact/access/audit interfaces. P4 owns registry/composition/connectors and combined checks coordination. Handoffs are versioned ports, with current authorization checked at command/read/completion.

Windows is code/lightweight checks; missing dependencies are `REQUIRES_LIGHTNINGAI_TEST`. Approved LightningAI work uses the separate Sketch2Life environment and preserves the existing Wan2.2 environment. Fixture readiness, real inference, durable runtime and visual/device evidence are separate gates.

Source audit: `evidence/notes/SOURCE_AUDIT.md`. Full task order: `plan/BE2_ROADMAP.md`. Next gate: explicit Phase A revision 1 approval. This request authorizes planning; generated approval placeholder remains AWAITING_APPROVAL and grants no runtime scope.

## Claude handoff amendment — 2026-10-14

User asked “Cụ thể làm như nào và BE này cho claude làm nha”. Claude is the requested BE2 implementation agent; human team ownership remains P3/BE2. `plan/CLAUDE_BE2_HANDOFF.md` provides six concrete batches, review/implementation prompts and an optional explicit Phase A approval message for the user to send. Assignment is recorded separately from runtime approval. Claude CLI is present in command inventory; no Claude model task has been invoked in this handoff change.

Plan revision 1 remains unapproved and was clarified: full SRS command idempotency scope includes principal identity; semantic dedup is separate; fake auth/provider composition stays in isolated fixture/test app. Implementation status remains NOT_STARTED. Handoff evidence: `evidence/notes/CLAUDE_HANDOFF_REVIEW.md`.

## Phase A implementation — 2026-10-14 (Claude)

User approved BE2-01 Phase A per `plan/PLAN.md` revision 1 and assigned A1–A9 to Claude; the
approval and verbatim instruction are recorded in `approvals/TASK_APPROVAL.md` before code.
Candidate decisions written first in `plan/PHASE_A_CANDIDATE_SPEC.md`.

Delivered (fixture scope only): pure DATA-25 domain, completion guards, ProviderCopyLifecycle
domain; ports; application service (scoped idempotency, semantic dedup, outbox dispatch,
start/progress/completion/timeout/retry/cancel/notices, CMD-44 projection); DATA-25/24,
ProviderCopyLifecycle and shape-spec candidate contracts; staged-transaction fakes; thin CMD-44
router mounted only in an isolated fixture app; 63 synthetic fixtures + manifest; offline runner;
four test files. Live `app.py`, legacy jobs/contracts and the Gradle wrapper edit are untouched.

Verification receipts: `evidence/notes/PHASE_A_IMPLEMENTATION_EVIDENCE.md`. Handoff pack:
`evidence/notes/PHASE_A_HANDOFF.md`. Phase A results are fake/contract semantics only; BE2-01 is
not DONE (Phase B durable work, adoption checkpoints and independent review remain). No commit,
push, deploy, dependency install or provider call was made.

## Independent Phase A implementation review — 2026-10-14 (Codex)

Latest review result **NEEDS_REVISION**; overall feature stays IN_PROGRESS with Phase A approval unchanged. Independent rerun reproduced 172 tests passed/1 skipped and 171 runner checks passed. Fresh probes found one P1, nine P2 and one P3 issue, including foreign-artifact quarantine, semantic scope dedup, completion receipt poisoning, malformed failure polling, provider-copy concurrency/replay and contract/poll consistency. Existing fixtures passing does not establish closure of these defects.

Full findings/probe receipts: `evidence/notes/PHASE_A_CODEX_INDEPENDENT_REVIEW_20261014.md`. Ready-to-send Claude correction prompt: `plan/CLAUDE_PHASE_A_FIX_PROMPT.md`. Codex changed review documents/evidence only; Claude retains implementation/fix responsibility. Next step: fix Phase A and re-review, then P1/P2/P4 candidate adoption/missing dependency gates. No Phase B activation or new approval is inferred.

## BE2 roadmap and scope-control amendment — 2026-10-14

Direct user request: “G hãy phân tích lại toàn bộ task cho BE2 này và sau đó làm 1 roadmap lộ trình làm và sẽ bám sát theo lộ trình đó để tránh phát sinh phình to task ra”. Documentation analysis is authorized; runtime approvals remain unchanged.

Current execution routing: `plan/BE2_ROADMAP.md` revision 2; progress/blockers/scope changes: `plan/BE2_EXECUTION_TRACKER.md`. This pair supersedes loose next-task recommendations in old handoffs, but does not supersede SRS/FEAT-040 requirements or approved Phase A plan. Exactly 14 business cards; one active implementation card/checkpoint; current slot Q00 Phase A corrections. Default queue, bounded decision/model fallback, per-card outputs/exclusions/exits, role ownership and change-control are recorded.

Remaining cards use own feature plan/approval before code; 01-B remains separate runtime gate. Model/storage choices, schema adoption and actual generation/deletion evidence are preserved, not inferred from roadmap. Claude implements, Codex plans/reviews. No backend code, approval, approved Phase A PLAN.md, canonical SRS or FEAT-040 task bytes changed by this roadmap work. Revision1 roadmap is archived as evidence; review/verification in evidence/notes/BE2_ROADMAP_REV2_VALIDATION_20261014.md.

## Q00 review corrections — 2026-10-14 (Claude)

Independent review NEEDS_REVISION (R01–R11) was addressed inside the existing Phase A revision 1
approval, ACTIVE slot Q00. Each finding was reproduced first (`raw/q00_repro_before.json`), fixed
in its owning module, and covered by `backend/tests/unit/test_ai_job_review_regressions.py`,
runner checks and 27 new negative fixtures (`raw/q00_repro_after.json`: all absent). Candidate
spec and handoff carry “(Q00)” amendments. All Phase A gates re-ran with exit 0. Status stays
IN_PROGRESS: independent closure review, P1/P2/P4 adoption and the Pillow-dependent live-route
check remain. Evidence: `evidence/notes/PHASE_A_Q00_FIX_EVIDENCE.md`. No commit/push.
## Q00 closure review amendment — 2026-10-14 (Codex)

Original R01–R11 repros independently resolved after Claude fixes. Overall NEEDS_REVISION for three focused corrections: R03a accepted result still quarantined, R04a unhashable provider code normalization, A18a pre-existing cancel/purge stale-save gap in the existing lifecycle invariant. Current tests236 pass/1 skip; runner217 checks pass. ACTIVE Q00 and approved scope remain unchanged; no new business card. Latest review: evidence/notes/PHASE_A_Q00_CODEX_CLOSURE_REVIEW_20261014.md; next prompt: plan/CLAUDE_Q00_FOLLOWUP_FIX_PROMPT.md. Consumer adoption/Pillow/runtime gates remain separate. Code executor remains Claude; Codex changed review records only.

## Q00 closure follow-ups — 2026-10-14 (Claude)

Closure review confirmed R01–R11 original cases closed and raised R03a/R04a/A18a. All three were
reproduced first (`raw/q00a_repro_before.json`), fixed in their owning modules and covered by
`backend/tests/unit/test_ai_job_q00_followups.py` plus runner checks (`raw/q00a_repro_after.json`:
absent; original R01–R11 repro still absent). Candidate spec/handoff amended (artifact
`quarantine_reason`, temporary vs final rejection, cancel under `scope_lock`). Final gate set
`q00a_run3` all exit 0. Executor status FIXED_PENDING_REVIEW; Q00 stays ACTIVE, BE2-01
IN_PROGRESS. Evidence: `evidence/notes/PHASE_A_Q00_FOLLOWUP_FIX_EVIDENCE.md`.

## Final Q00 code review — 2026-10-14 (Codex)

Latest code review **PASS at Phase A fake/contract scope** supersedes the earlier NEEDS_REVISION results: original R01–R11 cases and focused R03a/R04a/A18a are independently CLOSED. Reproduced 255 tests passed/1 Pillow skip, runner222 checks/0 failures, original11 and follow-up3 repros clear; independent claim/copy reviewers confirmed closure. No remaining code correction is requested in this reviewed scope.

ACTIVE Q00 now waits only for named P1/P2/P4 candidate contract/port adoption and the live-app route check in a compatible existing environment (or explicit checkpoint acceptance deviation). Overall Phase A acceptance remains PENDING; whole BE2-01 IN_PROGRESS. Q01 Phase B needs its own reviewable plan, persistence/queue/transaction/recovery ADR, BE1 ports and approval before code. Earlier dated snapshots are history, not current routing. Approval/approved PLAN.md/source requirements preserved; Codex changed review/tracking records only. Evidence: evidence/notes/PHASE_A_Q00_FINAL_CODE_REVIEW_20261014.md.

## Concrete Q00 gate handoff — 2026-10-14

Owner asks “Cụ thể làm như nào ?”. plan/CLAUDE_Q00_ACCEPTANCE_PROMPT.md gives Claude a bounded documentation/read-only check work order: reconcile candidate handoff, prepare named P1/P2/P4 review/disposition record and run exactly the remaining live-app route test only in an existing compatible authorized environment. A9/A-20 is cross-review/handoff at candidate/fixture level; production adoption can stay deferred by an explicit checkpoint decision. No live consumer implementation or production-policy freeze is added to Phase A. Test PASS requires 1 passed/0 skipped; exit0 with a Pillow skip does not close the gate. Current gates remain pending until genuine evidence/decisions arrive; backend/approved plan/approval unchanged.

## Q00 acceptance gates — 2026-10-14 (Claude)

Handoff synced with the final code review; acceptance gate record created (`evidence/notes/PHASE_A_ACCEPTANCE_GATE_RECORD.md`) with
P1/P2/P4, BE2-05/BE2-14 and task-owner rows, evidence hashes and the exact question per owner.
No existing owner/consumer decision was found, so all decision cells are PENDING_OWNER_DECISION
(DATA-24 and ProviderCopyLifecycle DEFERRED_TO_OWNING_CARD). The live-app route test was executed
with the exact command in the reviewed venv: exit 0 but **1 skipped** (Pillow) → NOT_RUN /
REQUIRES_LIGHTNINGAI_TEST; no local interpreter has pytest + FastAPI + Pillow and none was
installed or spliced. Reviewed source hashes unchanged. ACTIVE Q00; Phase A acceptance PENDING;
whole BE2-01 IN_PROGRESS. Backend code, PLAN.md and TASK_APPROVAL.md unchanged.

## Q00 delivery review and Phase B planning preparation — 2026-10-14 (Codex)

Owner steers “tiếp tục đi”. Codex verified 24 frozen source/test/runner/approval/plan hashes and delivered gate evidence; live-route remains 1 skipped/NOT_RUN. Consumer/task-owner decisions are pending. Focused handoff/gate wording now distinguishes candidate P2 review from Phase B capability/adoption, fixture A20 checks from actual consumer review, and output admission from owned-ref quarantine. No backend code or approval changed.

plan/CLAUDE_PHASE_B_PLANNING_PROMPT.md is ready for a documentation-only Claude turn, independently of the pending Q00 gates. It requests a proposed Phase B plan/ADR/port review, preserves ACTIVE Q00 and all implementation prerequisites; no Phase B code approval is inferred from continuation. Review: evidence/notes/Q00_ACCEPTANCE_DELIVERY_REVIEW_20261014.md.

## Phase B planning — 2026-10-14 (Claude, docs only)

Prepared plan/PHASE_B_PLAN.md (rev 1), plan/PHASE_B_ADR_PROPOSAL.md, plan/PHASE_B_PORT_REVIEW.md per `plan/CLAUDE_PHASE_B_PLANNING_PROMPT.md`. Findings: no DB/queue/
migration code exists (`infrastructure/db|persistence|queue` empty, no Alembic env); PostgreSQL,
SQLAlchemy/Alembic and Redis/RQ are ADR-0003 entries that ADR-0014/0015 downgrade to reuse
candidates for the replacement scope; BE1-02 generic persistence is not implemented. The plan
re-proposes those candidates for BE2 durable jobs only (D1–D6 PROPOSED), defines six batches B1–B6,
acceptance B-01..B-12 mapped to SRS B22.1/B22.3/B19.11/DATA-25/P-NFR-04/FIX-NFR-03 and the BE2-01
card, crash windows (no exactly-once claim) and minimal port changes. Plan status
PLANNED/AWAITING_APPROVAL; implementation NOT_STARTED. ACTIVE slot remains Q00; Q01 is
PLAN_PREPARATION only. No code, install, DB/broker start, cloud run or source upload.

## Independent Phase B plan review — 2026-10-14 (Codex)

Rev1 plan review NEEDS_REVISION for six bounded design corrections: owner decision fencing versus job CAS; SQL semantic NULL uniqueness and whole loser rollback; queued worker-start/ack and output recovery; attempt-bound capability contract/lifecycle; conflict/rejection audit durability; full notice coverage with bounded queries. These are implementability gaps in proposed Phase B changes, not reopened Phase A code findings or new business cards. Current source/SRS traces, official PostgreSQL17 docs and installed RQ2.11.0 were inspected; no Phase B runtime tests/services were run.

Claude remains executor for the docs revision. plan/CLAUDE_PHASE_B_PLAN_REVISION_PROMPT.md requests revision2 and consistent ADR/port/acceptance updates only. Rev1 proposals, approved PLAN.md/TASK_APPROVAL.md and the 24 reviewed Phase A source/test/runner files are unchanged by this review. Q01 implementation remains NOT_STARTED/UNAPPROVED; ACTIVE Q00 still waits for its checkpoint decisions and missing-test disposition. Review: evidence/notes/PHASE_B_PLAN_CODEX_REVIEW_20261014.md.

## Phase B plan revision 2 — 2026-10-15 (Claude, docs only)

Codex review of plan rev 1 was NEEDS_REVISION (PB-R01–R06). Rev 1 archived byte-identical
(`evidence/notes/PHASE_B_PLAN_REV1_ARCHIVE_20261014.md`); plan, ADR proposal and port review
updated to revision 2: owner-decision fence protocol (new D7, P2 Q8), canonical semantic key +
full losing-create rollback, receive/start/ack boundaries with SQL same-attempt reconciliation and
lease-generation fencing, attempt-bound typed capability, durable incident audit with `event_id`,
atomic all-match notices. Six batches and B-01..B-12 kept (subcases added). Findings
ADDRESSED_PENDING_REVIEW (`evidence/notes/PHASE_B_PLAN_REVISION_EVIDENCE.md`). Plan PLANNED/AWAITING_APPROVAL; implementation
NOT_STARTED; ACTIVE Q00 unchanged. No code, install, service start, cloud or contact.

## Focused Phase B rev2 closure — 2026-10-15 (Codex)

The six original plan cases are CLOSED_ORIGINAL_PLAN_CASE after independent persistence/dispatch review. Plan scope remains six batches/14 cards. Overall review still NEEDS_REVISION for only two grouped implementation-contract corrections: PB-C01 explicitly lists the pure queued DISPATCH_LOST transition/final-budget/race behavior and domain file delta; PB-C02 supplies transient capability and stable quarantine event-id carrier contracts/fake compatibility. These arise directly from rev2's selected mechanisms; no new platform/card/provider/real owner implementation is requested.

Latest review evidence/notes/PHASE_B_REV2_CLOSURE_REVIEW_20261015.md; next Claude docs prompt plan/CLAUDE_PHASE_B_REV2_COMPLETION_PROMPT.md requests revision3. Rev2 proposals retained unchanged by review; verified all24 Phase A source/test/runner/approval/approved-plan hashes and rev1 archive. Owner-fence closure is conditional on adopted D7/Q8, fixture proof labelled ASSUMED_CONTRACT; actual owner integration still B12 pending. ACTIVE Q00/Phase A acceptance gates remain; Phase B NOT_STARTED/UNAPPROVED.

## Phase B plan revision 3 — 2026-10-15 (Claude, docs only)

Rev 2 closure review closed PB-R01–R06 at design scope and asked for PB-C01/PB-C02 only. Rev 2
archived byte-identical (`evidence/notes/PHASE_B_PLAN_REV2_ARCHIVE_20261015.md`); plan/ADR/port
review now revision 3: pure queued-only `record_dispatch_loss` domain transition (Δ13), transient
`WorkerDispatchEnvelope` + `WorkerCapabilityIssuer` (Δ14), `QuarantineIntent` with stored
`event_id` (Δ15), “authoritative settlement” wording in Δ9. B1–B6/B-01..B-12 kept (subcases only).
Findings ADDRESSED_PENDING_REVIEW (`evidence/notes/PHASE_B_PLAN_REV3_EVIDENCE.md`). Plan PLANNED/AWAITING_APPROVAL;
implementation NOT_STARTED; ACTIVE Q00 unchanged; D1–D7/Q1–Q8/policy/env still PROPOSED/PENDING.

## Temporary publication selection — 2026-10-15

Direct user request authorizes provisional file triage:364 GitHub candidates,61 operator-local intermediate diagnostics and one separate Gradle change in the original426-file snapshot. evidence/notes/PUBLICATION_SELECTION_20261015.md records policy/original local hashes. Selected diagnostics stay at the same paths; source/test/runner/fixture/approved-plan/approval bytes are preserved. .gitignore hides only selected untracked diagnostics and feature-local operator reports. No stage/commit/push, new runtime scope or approval. Root branch's five unrelated changes are untouched. Actual validation/manifests live under evidence/local/publication-triage-20261015/.

## Final Phase B revision3 plan review — 2026-10-15 (Codex)

Focused independent reviewers confirm PB-C01 pure queued dispatch-loss transition and PB-C02 exact transient capability/quarantine-id carriers CLOSED. Revision3 plan review PASS; all original review cases remain closed. Exact rev3 plan/ADR/port bytes and rev1/rev2 archives are preserved, as are24 Phase A source/test/runner/approved-plan/approval hashes and61 local triage originals. No runtime tests/code/adoption/approval from this review.

Next independent step is B1 gate/decision preparation through plan/CLAUDE_PHASE_B_B1_GATE_PROMPT.md; no further plan-fix loop is requested. Phase A disposition, D1–D7/Q1–Q8 adoption/answers, test environment/profile and separate Phase B approval remain pending. ACTIVE Q00; Q01 plan review PASS waiting gates, implementation NOT_STARTED. Evidence: evidence/notes/PHASE_B_PLAN_FINAL_REVIEW_20261015.md. Existing B-05e/B-10c logging acceptance must cover structured RQ exception args as well as formatted logs during implementation; no new plan blocker.
