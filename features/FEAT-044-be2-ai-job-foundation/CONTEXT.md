# BE2 AI/job foundation context

## Publication for the second BE2 executor —2026-10-16

User now authorizes focused commits and push on the existing foundation feature branch to hand
off the checkpoint. DECISIONS125 records the instruction. Earlier "no commit/push" observations
below describe the review turn and are superseded for this publication only. Runtime/closure
remain pending on Studio; no dev merge or other-card implementation is implied. Sender01–07,
teammate08–14; repository handoff: artifacts/BE2_08_14_TEAMMATE_HANDOFF.md.

## Current checkpoint: A17-fix01 received cloud evidence —2026-10-16

**Q01/B6_A17FIX01_CLOUD_RECEIPTS_VERIFIED_PENDING_STUDIO**. Codex received archive3bcaa058
and verified raw cloud receipts:221 B2–B6 +224 Phase A /0 failure/error/skip;43/43 required
durable PASS. Exact two-file A17 scenario correction is ported locally;46/46 source hashes
match manifest5b76868d;25 local B6 units, focused ruff/mypy PASS. This is received remote
evidence, not direct local runtime or Studio proof. New A17-fix01 Studio execution NOT_RUN;
B6-CR01 open, BE2-01 IN_PROGRESS, B-12 HANDOFF, OwnerFence ASSUMED_CONTRACT. No approval/Git
publication change. See evidence/notes/PHASE_B_B6_A17FIX01_CLOUD_RECEIPT_REVIEW_20261016.md.
Earlier checkpoint and next-run instructions below are historical; use the A17-fix01 package
for the next Studio run, preserving all older packages.

## Local checkpoint decision —2026-10-16

Checkpoint **Q01/B6_CR01_R2_CODE_PACKAGE_REVIEW_PASS_PENDING_RUNTIME** is unchanged. Person 2 allowed
local commits of the reviewed Phase B state before the r2 Studio run because the Lightning Studio is
not usable (DECISIONS 124). This saves progress and is not acceptance: runtime r2 NOT_RUN, B6-CR01 open
(FIXED_PENDING_RUNTIME_REVIEW), BE2-01 IN_PROGRESS, B-12 HANDOFF, OwnerFence ASSUMED_CONTRACT, no
P1/P2/P4 sign-off, approvals unchanged. The Studio keeps base 993a26c and source 90724453 and runs the
existing b6cr01r2 package later; results follow in a separate commit. No push, merge or deploy.
The older "ACTIVE" lines below are historical routing for their own dates.

## Codex R2 code/package pre-run review —2026-10-16

**Q01/B6_CR01_R2_CODE_PACKAGE_REVIEW_PASS_PENDING_RUNTIME** on 46-file manifest cb527d7f and ZIP 3a9d6ef2. The reviewed source is runner d42d697c / B6 unit b1d3bced. Independent local21 B6 tests PASS; heldout missing B2-B6/Phase A parameter variants are NOT_RUN; unmapped failure with a missing variant yields FAIL/exit1; collection errors fail closed. R2 package audit PASS: 46/46 current hashes, ZIP4 members, two-file delta from90724453, scratch apply/reverse, shell syntax, source-state pins and exit/skip guards. No actionable finding remains in this focused pre-run scope. Studio runtime is NOT_RUN; CR01 remains FIXED_PENDING_RUNTIME_REVIEW, not closed. See evidence/notes/PHASE_B_B6_CR01_CODEX_PRECOMMIT_REVIEW_20261016.md, latest R2 addendum. Next: run only b6cr01r2 on the approved synthetic Studio, review the source-bound results, then refresh publication documents and dry run. BE2-01 IN_PROGRESS, B-12 HANDOFF; approvals and source/packages unchanged by review. No staging/commit/push/merge/deploy.

Earlier checkpoints follow.


- Updated 2026-10-16, Asia/Saigon. Phase A ACCEPTED_CANDIDATE_FIXTURE.
- ACTIVE (independent closure review, 2026-10-16): **Q01/B6_CLOSED_WITH_NOTES** at component
  scope on manifest 90724453; Phase B B1–B6 component-closed; B-12 HANDOFF; BE2-01 IN_PROGRESS,
  not DONE. See "B6 independent closure review" at the end of this file.
- Superseded routing (the lines below predate B6 and were not refreshed during B6):
- ACTIVE **Q01/B6_READY_FOR_HANDOFF**; **B5_CLOSED_REVIEW_PASS**.
  **B5-R01/B5-R02/B5-RT01 CLOSED_B5_SCOPE** after source-bound runtime and focused closure.
- USER_REPORTED_REMOTE fix03 run 2026-10-15T17:37:09Z (2026-10-16 00:37:09 Asia/Saigon): 193 B2-B5 passed / 0 failed / 0 skipped; 224 Phase A passed / 0 skipped; fixture 20 PASS / 215 checks / d17f58a3 unchanged (optional HTTP NOT_RUN 1). All suite/log/outer/Studio exits 0, RUNNER_RESULT=PASS. 43 source files verified as fix03 3930046b; local and reported Studio source match.
- Current source manifest: 3930046b5f04a67b6ff2a52dc70a4f12d5d7a89c2675e149ab654f00da2ab670; base 993a26cae78c0a4fe983033f03881838c886b176.
- Closure review: evidence/notes/PHASE_B_B5_CLOSURE_REVIEW_20261016.md; matching evidence/metrics/PHASE_B_B5_CLOSURE_REVIEW_20261016.json. Prior fix02 failure and local NOT_RUN records remain historical.
- B6 NOT_STARTED: conformance runner, crash-point matrix, Phase A scenarios on SQL, consolidated report and handoff under existing approved Phase B revision 3 B1-B6. Claude first rehydrates read-only from latest handover section AA, reports and stops; B6 implementation follows the agreed separate continuation message, without repeat approval.
- Parent BE2-01 IN_PROGRESS; exactly 14 business cards / WIP 1 / full-card DONE 0. B1-B5 closed at their recorded component scopes, not whole-product completion. OwnerFence ASSUMED_CONTRACT; real P1/P2/P4 integration/B-12, providers, live router and production adoption remain deferred. No other card, FEAT-018/Wan, install, service recreation, staging, commit, push or deploy. Original approvals/plans/ADR unchanged.

## Current approval handoff —2026-10-15

Actual user reply accepts Phase A candidate/fixture, accepts rev8 §13 as PROJECT_OWNER_DIRECTIVE
and approves Phase B planrev3 B1–B6 on the named Studio. The user explicitly requests a separate
Phase B approval record, preservation of Phase A approval, B2-first implementation and review
before B3. Canonical verbatim source: approvals/PHASE_B_TASK_APPROVAL.md. B1 reconciliation:
evidence/notes/PHASE_B_B1_CLOSURE_AND_HANDOFF_20261015.md. Earlier entries retain their dated state.

## Historical planning context snapshot —2026-10-14

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

Full findings/probe receipts: `evidence/notes/PHASE_A_CODEX_INDEPENDENT_REVIEW_20261014.md`. Ready-to-send Claude correction prompt: `evidence/local/claude/prompts/CLAUDE_PHASE_A_FIX_PROMPT.md`. Codex changed review documents/evidence only; Claude retains implementation/fix responsibility. Next step: fix Phase A and re-review, then P1/P2/P4 candidate adoption/missing dependency gates. No Phase B activation or new approval is inferred.

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

Original R01–R11 repros independently resolved after Claude fixes. Overall NEEDS_REVISION for three focused corrections: R03a accepted result still quarantined, R04a unhashable provider code normalization, A18a pre-existing cancel/purge stale-save gap in the existing lifecycle invariant. Current tests236 pass/1 skip; runner217 checks pass. ACTIVE Q00 and approved scope remain unchanged; no new business card. Latest review: evidence/notes/PHASE_A_Q00_CODEX_CLOSURE_REVIEW_20261014.md; next prompt: evidence/local/claude/prompts/CLAUDE_Q00_FOLLOWUP_FIX_PROMPT.md. Consumer adoption/Pillow/runtime gates remain separate. Code executor remains Claude; Codex changed review records only.

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

Owner asks “Cụ thể làm như nào ?”. evidence/local/claude/prompts/CLAUDE_Q00_ACCEPTANCE_PROMPT.md gives Claude a bounded documentation/read-only check work order: reconcile candidate handoff, prepare named P1/P2/P4 review/disposition record and run exactly the remaining live-app route test only in an existing compatible authorized environment. A9/A-20 is cross-review/handoff at candidate/fixture level; production adoption can stay deferred by an explicit checkpoint decision. No live consumer implementation or production-policy freeze is added to Phase A. Test PASS requires 1 passed/0 skipped; exit0 with a Pillow skip does not close the gate. Current gates remain pending until genuine evidence/decisions arrive; backend/approved plan/approval unchanged.

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

evidence/local/claude/prompts/CLAUDE_PHASE_B_PLANNING_PROMPT.md is ready for a documentation-only Claude turn, independently of the pending Q00 gates. It requests a proposed Phase B plan/ADR/port review, preserves ACTIVE Q00 and all implementation prerequisites; no Phase B code approval is inferred from continuation. Review: evidence/notes/Q00_ACCEPTANCE_DELIVERY_REVIEW_20261014.md.

## Phase B planning — 2026-10-14 (Claude, docs only)

Prepared plan/PHASE_B_PLAN.md (rev 1), plan/PHASE_B_ADR_PROPOSAL.md, plan/PHASE_B_PORT_REVIEW.md per `evidence/local/claude/prompts/CLAUDE_PHASE_B_PLANNING_PROMPT.md`. Findings: no DB/queue/
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

Claude remains executor for the docs revision. evidence/local/claude/prompts/CLAUDE_PHASE_B_PLAN_REVISION_PROMPT.md requests revision2 and consistent ADR/port/acceptance updates only. Rev1 proposals, approved PLAN.md/TASK_APPROVAL.md and the 24 reviewed Phase A source/test/runner files are unchanged by this review. Q01 implementation remains NOT_STARTED/UNAPPROVED; ACTIVE Q00 still waits for its checkpoint decisions and missing-test disposition. Review: evidence/notes/PHASE_B_PLAN_CODEX_REVIEW_20261014.md.

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

Latest review evidence/notes/PHASE_B_REV2_CLOSURE_REVIEW_20261015.md; next Claude docs prompt evidence/local/claude/prompts/CLAUDE_PHASE_B_REV2_COMPLETION_PROMPT.md requests revision3. Rev2 proposals retained unchanged by review; verified all24 Phase A source/test/runner/approval/approved-plan hashes and rev1 archive. Owner-fence closure is conditional on adopted D7/Q8, fixture proof labelled ASSUMED_CONTRACT; actual owner integration still B12 pending. ACTIVE Q00/Phase A acceptance gates remain; Phase B NOT_STARTED/UNAPPROVED.

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

Next independent step is B1 gate/decision preparation through evidence/local/claude/prompts/CLAUDE_PHASE_B_B1_GATE_PROMPT.md; no further plan-fix loop is requested. Phase A disposition, D1–D7/Q1–Q8 adoption/answers, test environment/profile and separate Phase B approval remain pending. ACTIVE Q00; Q01 plan review PASS waiting gates, implementation NOT_STARTED. Evidence: evidence/notes/PHASE_B_PLAN_FINAL_REVIEW_20261015.md. Existing B-05e/B-10c logging acceptance must cover structured RQ exception args as well as formatted logs during implementation; no new plan blocker.

## Phase B B1 decision record — 2026-10-15 (Claude, docs only)

Per `evidence/local/claude/prompts/CLAUDE_PHASE_B_B1_GATE_PROMPT.md`, one reviewable record `plan/PHASE_B_DECISION_RECORD.md` (rev 1) gathers
G1 (Phase A rows reused from the gate record, not re-asked), G3 ADR D1–D7 + ADR location with exact
D3/D7-alternative deltas, G4 the eight existing P2/P4 questions (Q7 environment deduplicated into
G5), G5 environment/inventory/secret mechanism/fixture profile `fixture.durable_jobs.v0`
(PROPOSED, fixture only) and G2 preconditions with a sample approval marked not-an-approval.
Searched repo/session: no P1/P2/P4 role-owner record and no project-owner decision for G1/G3/G4/G5;
only policy-level directives (environment policy 2026-10-10, ADR-0015 roles) apply as constraints.
Status PENDING_OWNER_DECISION. B1 sequence diagrams NOT_STARTED (depend on D3/D7). ACTIVE Q00;
Q01 PLAN_REVIEW_PASS_WAITING_GATES; Phase B code NOT_STARTED/UNAPPROVED. The concurrent
user-approved EOF fix (`evidence/notes/Q00_FOLLOWUPS_EOF_DISPOSITION_20261015.md`) was left as is.

## Scoped B1 record review — 2026-10-15 (Codex)

Decision record rev2 clarifies genuine project-owner directives versus role-owner concurrence
for Q8/D7. No owner decision was added; actual P2 integration remains B-12 pending. Proposed
diagrams can be prepared before adoption from the reviewed preferred D3/D7; B1 exit still
needs actual decisions and adopted ADR. Next Claude docs work:
`evidence/local/claude/prompts/CLAUDE_PHASE_B_B1_DIAGRAM_PROMPT.md` (one evidence file, seven flows/crash-window table).
Review: `evidence/notes/PHASE_B_B1_DECISION_RECORD_REVIEW_20261015.md`. Plan rev3 PASS unchanged;
ACTIVE Q00; Phase B code NOT_STARTED/UNAPPROVED. Verified all24 HEAD hashes and only the existing
one-newline working-tree disposition. No source/test/approval/install/service/publication change.

## Phase B B1 proposed sequences — 2026-10-15 (Claude, docs only)

`evidence/notes/PHASE_B_B1_PROPOSED_SEQUENCES.md` drafts the seven B1 flows (create, dispatch/receive/start, completion, retry/recovery,
Teacher cancel, owner notice, incident audit) as Mermaid sequences plus the crash-window table
(all ten §7.1 rows + §7.2/Δ10 windows), against preferred D3 Redis/RQ and D7 shared-transaction
fence, bound to plan/ADR/port rev3 and decision record rev2 hashes. Labelled PROPOSED /
NOT_ADOPTED / NOT_RUNTIME_EVIDENCE; owner fence ASSUMED_CONTRACT; five assumptions (A1–A5) noted
in the file, no plan change. Merged BE1 code (`8b2a1ad`) observed as context only (A5), not a
D2/Q1/Q7 decision. **B1 exit still PENDING** actual decisions/adopted ADR and reconciliation.
ACTIVE Q00; Q01 waiting gates; WIP 1; 14 cards; BE2-01 IN_PROGRESS.

## B1 sequence review completed — 2026-10-15 (Codex)

Diagram draft rev2 has passed focused independent persistence/dispatch re-review after bounded
receipt/control-flow, dispatch-fence/ack/recovery and incident-bundle clarifications. Plan/ADR/
port rev3 remain unchanged. Decision record rev3 updates prepared status and proposes ADR-0018
(recheck availability) because merged BE1 occupies0016/0017. No owner input/adoption is inferred.
Harness/security/diff are now PASS after the separately applied six BE1 placeholders; the old
Claude harness failure remains historical. No backend/test/fixture/approval change here.
Next: actual decisions in plan/PHASE_B_DECISION_RECORD.md, then adopted ADR/environment evidence
and separate Phase B approval. No additional planning batch. ACTIVE Q00/Q01 waiting; B1 exit
pending; runtime/Mermaid render NOT_RUN. Evidence is in the diagram §12 and sequence-review metrics.

## Owner architecture selection and inventory request — 2026-10-15

Owner replied "Ổn đó" to the concrete preferred D1–D7/fixture-first/current fixture profile and
test-first Phase A recommendation. Recorded verbatim with separate contextual interpretation as
O-01 in decision record rev4; architecture accepted in docs/adr/ADR-0018-be2-durable-ai-job-runtime.md.
No blanket Q1–Q8 answer, role concurrence, Phase A acceptance or Phase B code approval inferred.
Owner then answered "Chưa rõ; cần kiểm kê môi trường hiện có" (O-02). Read-only inventory proceeds;
target E1/E2 and install/start/provisioning remain undecided. Remaining contract details and actual
test/checkpoint disposition stay open. ACTIVE Q00; Q01 waiting remaining gates, WIP1/14 cards.

Read-only local inventory: Windows service metadata labels PostgreSQL18 RUNNING; actual server
version/connection not queried. Docker CLI present but engines inaccessible; no Redis confirmed;
Pillow missing. WSL/listener enumeration denied in this session. No named Linux/LightningAI target
was supplied, so G5 remains NOT_VERIFIED. Next Claude read-only handoff is
evidence/local/claude/prompts/CLAUDE_PHASE_B_ENVIRONMENT_INVENTORY_PROMPT.md; no setup/start/install or code authorized.

Owner O-03 selects a new CPU Studio separate from FEAT-018; proposed name sketch2life-backend-test. Decision record rev5 captures the exact reply. No Lightning tools/authenticated target available here, so creation has not occurred; target/service inventory and server provisioning remain pending.

Remote environment O-04 (user-supplied output): new Studio reported created, Linux6.8x86_64/Docker28.0.1 daemon available, no running containers listed. Python3.14.7 is outside backend>=3.12,<3.14; proposed runner uses existing python:3.12-slim baseline. Next published BE2 checkout/runner verification, then isolated PostgreSQL17/Redis provisioning; no B2 code approved. See evidence/notes/PHASE_B_ENVIRONMENT_RECORD.md; decision record rev6.

O-05: user reports Python3.12.15 container runner success and image digest; no rows from docker ps -a.
Source checkout/commit still not provided. Prepared first-run dedicated PostgreSQL17/Redis8 bootstrap
in the reusable environment record; services are not yet reported started and no remote actions
were performed by Codex. Credential file stays outside Git, no host ports, existing names stop.
Next collect service readiness and branch/commit, then runner dependencies/connection/test proof.

O-06 user reports PostgreSQL17.11, Redis PONG and both dedicated containers healthy; retain them.
Git branch/log ran outside a repository (~), so checkout/commit still unresolved. Next reuse or
clone $HOME/Sketch2Life and verify with git -C, then runner dependencies/connection/Phase A test.
Decision record rev7; G5 partial only, no Phase B code/acceptance inferred.

O-07: user verifies published BE2 branch at shallow HEAD993a26c. Next isolated Python3.12 runner
setup uses backend[dev,image-admission] (live-app eager PyAV import), service connections and the
missing Phase A route test. Persistent venv volume, secret file readonly, receipts feature-local;
no provider/migration/B2 implementation. All runtime outcomes still pending user execution.

O-08: user supplies Python3.12.15/dependency inventory within declared bounds, PostgreSQL17.11/
Redis8.10.2 authenticated runner connections PASS, and exact live-route1 passed,0 skipped in2.72s
on published993a26c. Baseline environment ready by user report; no direct remote re-run claimed.
Gate record updated with actual test follow-up; earlier skip/history preserved. Decision record
rev8 §13 presents one proposed candidate/component Q1–Q8+synthetic-use/code-scope packet; not yet
approved. Next is one genuine project-owner directive/Phase B approval, then Claude B2-only first
turn via evidence/local/claude/prompts/CLAUDE_PHASE_B_IMPLEMENTATION_PROMPT.md. No further setup/planning batch or new card.

## O-09 execution handoff —2026-10-15

Approval and accepted candidate/component decisions are now real, not inferred from a test.
B1 closed at component scope; Claude receives B2 only. Current top summary/tracker supersedes
earlier pending gate entries. No backend implementation or remote execution occurred in this handoff.

## Phase B B2 schema/migration — 2026-10-15 (Claude, code)

Under the actual Phase B approval (B2 only): `infrastructure/ai_jobs/sql/tables.py` (schema `ai_jobs`,
seven plan §6 tables), Alembic revision `20261015_ai_0001` as an independent `ai_jobs` branch in the
existing `backend/alembic` env (BE1 `be1_core` history unchanged), env.py schema filter, and
`backend/tests/integration/ai_jobs` (6 offline checks pass; 8 PostgreSQL checks NOT_RUN locally).
Source snapshot = `993a26c` + patch sha256 `eb9d75bd…a5bab`; exact Studio procedure prepared, no remote
access from this session. State B2_CODE_COMPLETE — PostgreSQL checks NOT_RUN (REQUIRES_STUDIO_RUN). Plain `alembic upgrade head` now reports multiple heads;
backend READMEs use `be1_core@head`. Evidence: `evidence/notes/PHASE_B_B2_SCHEMA_MIGRATION_EVIDENCE.md`. No B3 code; no commit/push/deploy.

## Independent B2 review —2026-10-15

Claude delivered schema/migration/tests; local checks reproduce6 B2 passed/8 PostgreSQL skipped
and223 Phase A passed/1 local Pillow skip. NEEDS_REVISION only B2-R01 opaque-ID column widths
and B2-R02 Studio runner failure/retry behavior. Actual PostgreSQL NOT_RUN; keep B3 NOT_STARTED.
See evidence/notes/PHASE_B_B2_CODEX_REVIEW_20261015.md. This is correction within approved B2,
not another plan/card/approval round. Codex changes no backend/test/runner source in this review.

## Chuyen phien Claude theo yeu cau user —2026-10-15

User requests a complete old-session handover and a new-session bootstrap to avoid context loss.
Use evidence/local/claude/prompts/CLAUDE_WRITE_SESSION_HANDOVER_PROMPT.md: current Claude writes the actual session facts
plus verified repository state to two handoff/bootstrap documents; handover turn is docs-only,
not B2 fixes. Current Q01/B2 NEEDS_REVISION and actual Phase B approval remain unchanged.

## Claude session handover — 2026-10-15 13:10 +07:00 (docs only)

Session transfer, not a gate: `evidence/local/claude/handover/CLAUDE_SESSION_HANDOVER_20261015.md` (checkpoint, sources, decisions, file/package hashes, findings,
tests, Studio) and `evidence/local/claude/prompts/CLAUDE_NEW_SESSION_START_20261015.md` (paste-ready start prompt). Checkpoint unchanged: Q01 / B2 NEEDS_REVISION,
B2-R01/R02 OPEN, PostgreSQL B2 matrix NOT_RUN, B3 NOT_STARTED; no code changed by the handover.

2026-10-15, Codex, explicit user request after review: corrected the handover and new-session
bootstrap verbatim for path bases/required context reads, all-current-tests acceptance, unverified
remote migration provenance and scoped offline/mock PASS. Current Q01/B2 NEEDS_REVISION,
actual approval and implementation scope are unchanged. Correction receipts remain feature-local
under evidence/local/claude-session-handover-20261015/review-corrections/.

## Codex B2 takeover and corrected handover —2026-10-15

User explicitly asks Codex to continue after Claude limit and update the handover; exactsource
in evidence/notes/B2_CODEX_EXECUTOR_HANDOFF_20261015.md. Only five opaque-ID widths in metadata/
migration and related boundary tests changed in backend; runner fixed locally and26 mock cases
PASS. B2suite8passed/10PGskipped, PhaseA223passed/1localPILskip; ruff/format/mypyPASS. Independent
code reviewsPASS at local/offline scope. PostgreSQL NOT_RUN; current package f388ce36…419bff,
patch/manifest/runnerZIP ready. New fix evidence+handover/bootstrap supersede old untouched-findings
and old package next steps. Approvals/plans/contracts/BE1/history/EOF/.gitignore/61localoriginals
preserved, no install/service mutation/provider/commit/push/deploy. Await actualStudio run then
final B2 closure review before B3, not another implementation/approval/planning round.

## Actual Studio B2 results and closure —2026-10-15

User supplies exact-package source/provenance, B2suite18passed/0skip (8offline+10PostgreSQL),
PhaseA224passed/0skip. Code/coverage/hash rechecks plus two independent closure audits PASS at
B2schema/migration scope. Source remains dirty993a26c+f388patch, unchanged by this closure.
Report provenance USER_REPORTED_REMOTE, not directCodexremoteexecution; finalphase_a_log_exit/
outerrunnerexit NOT_REPORTED, not assumed0. See evidence/notes/PHASE_B_B2_CLOSURE_REVIEW_20261015.md
and metrics/PHASE_B_B2_STUDIO_CLOSURE_20261015.json. R01/R02 CLOSED, B2_CLOSED_REVIEW_PASS,
nextB3READYcodeNOT_STARTED under existingB1–B6approval. Fullrestart/crash/conformance/actual
integration remainlaterbatches; no fullcardDONE or newcode/commit/push/deploy in closure.

## Two-step Claude continuation requested by user —2026-10-15

User chooses to wait for Claude availability and asks for updated handover plus two separate
pasteable steps. Step 1 (evidence/local/claude/prompts/CLAUDE_NEW_SESSION_START_20261015.md): new Claude reads actual
sources, checks workspace/approval/checkpoint with read-only operations, reports understanding,
then STOPS without edits/tests/packages/remote actions. Step 2, pasted later in the same session
(evidence/local/claude/prompts/CLAUDE_PHASE_B_B3_IMPLEMENTATION_PROMPT.md), executes approved B3 only and stops for review
before B4. Reading the B3 prompt during takeover is not an instruction to execute it in step 1.
This user-selected interaction creates no card/gate/approval and changes no approved plan.
B2 remains CLOSED_REVIEW_PASS; ACTIVE Q01/B3_READY_FOR_IMPLEMENTATION, B3 code NOT_STARTED.
No backend/tests/runner/services or original approvals changed by this documentation update.

## Phase B batch B3 implementation —2026-10-15

Claude implemented approved B3 only (user step 2 in the same session; existing Phase B rev3
approval, no new card/approval/plan revision). New `infrastructure/ai_jobs/sql/repository.py`
(READ COMMITTED UoW, plain INSERT → typed `UniqueConflict`, CAS, fence hold on the UoW connection,
held epochs in `job.accepted_fences`) and test-only `sql/owner_fence_fixture.py`
(ASSUMED_CONTRACT `owner_fence_fixture` schema: owner FOR UPDATE epoch+decision+withheld notice,
BE2 FOR SHARE). Ports/service/fakes gain Δ1–Δ5: fenced decisions, decide-before/hold-inside
rounds with one re-decision, canonical NFC semantic sha256, whole-candidate rollback and bounded
winner re-read, same-transaction audit intents for create/dedup/cancel. B2 migration and BE1
history untouched; no new revision. Local: Phase A 223 passed/1 Pillow skip, runner digest
identical to Q00 final, 22 offline B2/B3 passed, lint/type/validators exit0; 37 B3 + 10 B2
PostgreSQL cases NOT_RUN. Studio package b3 a2e479d5… (on top of B2 f388) and runner prepared for
the user. State B3_CODE_COMPLETE, PostgreSQL NOT_RUN; B4 not started; no commit/push/deploy.
Evidence: evidence/notes/PHASE_B_B3_REPOSITORY_FENCE_EVIDENCE_20261015.md.

## B3 reported Studio PASS and independent review —2026-10-15

User reports 69 B2+B3 passed/0skip (22 offline +37 B3 PG +10 B2 PG), all suite/log/outer/operator
exits0. Phase A count was not pasted; exit/log0 and skipgatePASS were. Default fixture20PASS/
215checks retains optional HTTP NOT_RUN. Preserve USER_REPORTED_REMOTE; source header/timestamp
and receipt directory were not pasted. Locally all19sourcehashes match the instructed a2e479d5
package; this is not direct Codex Studio execution or a new live-router/whole-Phase-B claim.

Independent primary/peer review finds one P2 defect, B3-R01: unlocked separate READ COMMITTED
job/attempt reads can combine commits. Offline actual mapping/projection/wire-validation probe
reproduces queued revision1 with started_at, rejected by the existing contract. Therefore current
Q01/B3_NEEDS_REVISION, not CLOSED; old tests remain PASS but lack this interleaving. Claude fixes
only the read coherence and regression per evidence/local/claude/prompts/CLAUDE_PHASE_B_B3_FIX_PROMPT.md, prepares a safe
old-B3-to-fixed-source package transition and obtains new runtime evidence/review before B4.
Review edited no backend/tests/runner; B2 closure and original approvals/plans preserved.
Same14cards/WIP1/full-cardDONE0; no install/service/provider/commit/push/deploy.

## Operator prompts kept local at user request —2026-10-15

Moved15Claude prompts and one session handover into ignored evidence/local/claude/; entry point
evidence/local/claude/INDEX.md. Active correction is now
evidence/local/claude/prompts/CLAUDE_PHASE_B_B3_FIX_PROMPT.md. Current references and operator
publication lists were updated; original bytes/hash/path map are retained in ignored
evidence/local/prompt-relocation-20261015/. Seven already-tracked prompt paths show deletions,
not staged changes. plan/CLAUDE_BE2_HANDOFF.md stays because actual Phase A approval references
it; approvals/plans/contracts/reviews/executor authorization remain repository evidence.
Backend/source/approved-plan/approval bytes and Q01/B3_NEEDS_REVISION remain unchanged.
No staging, history rewrite, commit, push, deploy or FEAT-018 change.

## Corrected-source Studio result and B3 closure —2026-10-15

User full log verifies corrected20-file manifest0814d514/deltaf38dd1fe after exact old snapshot:
71B2+B3passed/0skip (39B3PG+10B2PG+22offline),224PhaseApassed/0skip, allsuite/log/outer/operator
exit0; defaultfixture20PASS/215checks/d17f58a3digest retains optionalHTTPNOT_RUN. Provenance
USER_REPORTED_REMOTE; run2026-10-15T09:27:44Z,receipt run-20261015T092740Z-454946. Optional
before-helper collected0/IndexError/exit2: NOT_PROVEN_SETUP_ERROR, not reproduced despite its
historical label. Valid current regression/code review + prior independent offline defect probe
support B3-R01 CLOSED_B3_SCOPE and B3_CLOSED_REVIEW_PASS without another full-suite rerun.

Current Q01/B4_READY_FOR_IMPLEMENTATION, B4codeNOT_STARTED; Claude B4-only work order under
ignored evidence/local/claude/prompts/CLAUDE_PHASE_B_B4_IMPLEMENTATION_PROMPT.md. Existing PhaseB
approval remains valid, review before B5. B2 remains closed;14cards/WIP1/full-cardDONE0. Closure
changes docs/evidence only; backend/tests/runtimepackage/approval/approved-plan bytes preserved.
Current proof evidence/notes/PHASE_B_B3_CLOSURE_REVIEW_20261015.md and matching closure metric.

## B3-R01 fix —2026-10-15 (Claude)

Under the existing approval and `CLAUDE_PHASE_B_B3_FIX_PROMPT.md`, only B3-R01 is corrected:
`SqlAiJobUnitOfWork.get_job` reads job and attempts in one statement when unlocked (one READ
COMMITTED snapshot); the `for_update=True` path keeps lock-then-read. New PostgreSQL regression
`tests/integration/ai_jobs/test_aggregate_reads.py` pauses a start/retry writer before commit and
commits it between the reader's statements; the reader must return the exact pre-commit version
and a valid wire view. Local checks PASS; PostgreSQL NOT_RUN. Package
`evidence/local/b3r01-studio-package-20261015/` upgrades only the exact Studio snapshot
(manifest ea5cf57e) via a 2-file delta (f38dd1fe…) to manifest 0814d514… and first runs the new
regression on the old source (expected FAIL). The previous 69-pass Studio result stays recorded.
B3-R01 FIXED_PENDING_RUNTIME_REVIEW (still OPEN); B4 not started; no commit/push/deploy.

## Phase B batch B4 implementation —2026-10-15 (Claude)

Under the existing approval and the ignored B4 prompt, Claude implemented B4 only: Δ13 pure
`record_dispatch_loss`; Δ6 leased outbox claim (`SKIP LOCKED`, owner+generation) with a fenced
acknowledgement bundle (mark delivered + attempt `dispatched_at`/`dispatch_count`) under the job
row lock; per-row eligibility decision/fence hold before publish; Δ14 transient
`WorkerDispatchEnvelope` + `WorkerCapabilityIssuer`, minted outside SQL; `rq_queue.py` as the only
broker adapter (description=message_id, result_ttl 0, failure_ttl 60, no RQ retry); Δ7/Δ11
targeted reconciler sweeps with same-attempt republish up to 3 publishes, then dispatch loss.
Error catalogue regenerated for `DISPATCH_LOST` only. No schema change. Local Phase A/runner/
offline B2–B4/lint/type/validators PASS; 13 B4 + 49 B2/B3 PostgreSQL/Redis cases NOT_RUN.
Package `evidence/local/b4-studio-package-20261015/` (delta 44d98cd6…, manifest 70b2a160…)
upgrades only the closed B3 snapshot 0814d514. B4_CODE_COMPLETE, runtime pending; B5 not started.

## B4-RT01 package completion after Claude token limit —2026-10-15

User supplied full oldB4manifest70b2a160run:95collected/88pass/7fail/0skip, PhaseA224pass/0skip,
all7failures receiveremptyqueueValueError; environment rebuilt/healthy. Preserve USER_REPORTED_REMOTE.
Claude already wrote3-filelocalcorrection (RQfixtureLPOPNoneguard,typedinterval,unitregressions).
After user reports Claude unavailableuntil19:50, Codex completes only package/checks/handover:
no backend changes.32oldhashesreconstructed,3-filedelta44f3a80d,32newmanifest444cfead,
ZIPE1a76867.8host-only simulated runner flows PASS; local258pass/63skip (62PGRedis+1Pillow),
ruff/mypyPASS. CorrectedruntimeNOT_RUN; B4-RT01OPEN/FIXED_PENDING_RUNTIME_REVIEW, B5notstarted.
Nextupload newZIP to be2-b4rt01-package on existingStudio and run newrunner; current97cases
mustactuallyrun beforeindependentreview. Sameapproval/cards14/WIP1; no install/recreate/provider/
commit/push/deploy. Prompts/handover remain ignored evidence/local/claude/.

## Corrected B4 runtime and independent review —2026-10-15

User run2026-10-15T12:32:39Z verifies32-filemanifest444cfead/delta44f3a80d;
97B2–B4PASS/0skip+224PhaseAPASS/0skip, all exits0, fixture20PASS/215checks/d17f58a3digest with
optionalHTTP NOT_RUN1. Preserve USER_REPORTED_REMOTE. B4-RT01 CLOSED_FOR_REPORTED_SNAPSHOT.
Independent full review confirms one P2 B4-R01: first deferred full retry page indefinitely
starves later healthy work. Actual current-service51jobprobe and primary rerun confirm it;
this is localfake/service evidence, not a PG reproduction. B4_NEEDS_REVISION, B5notstarted.
Claude fixes only targeted paging/regression under existing approval via evidence/local/claude/prompts/CLAUDE_PHASE_B_B4_FIX_PROMPT.md.
Studio source is current444cfead; new fix needs bounded newpackage/evidence/review, not another
unchangedRT01run. B2/B3closed,14cards/WIP1/fullDONE0. See evidence/notes/PHASE_B_B4_CODEX_REVIEW_20261015.md.
Codex changed docs/evidence only; source/approval/approvedplans/packages preserved. No install,
service recreation, provider, staging, commit/push/deploy. Worker structured-log token redaction
remains existing B5 acceptance; real owner-fence ASSUMED_CONTRACT integration remains B-12.

## B4-R01 keyset-paged sweep fix —2026-10-15

Claude fixed only B4-R01 under the existing Phase B rev3 approval (Δ11). `_sweep` now pages with
a per-invocation keyset cursor: `now`/claim_limit fixed per invocation, strictly-after
`(sort time, unique id)` on the existing ORDER BY, stop on a short page, raise on an over-long
page. Fake and SQL parity; overdue/retry queries return `DueJob`. No persisted marker, scheduler,
larger LIMIT, full scan, retry-policy, fence, CAS, lock, RQ identity, contract or schema change;
blocked rows stay failed_retryable. Probe before `[[],[],[]]` -> after `[["job_fx0051"],[],[]]`.
Service regressions on rebuilt 444cfead: 2 failed / 3 passed; on the fix: 5 passed. Local Phase A
223 passed/1 skipped, B2–B4 40 passed/64 PG/Redis skipped (NOT_RUN), runner d17f58a3, lint/type/
validators PASS. Package b4r01 (444cfead -> f1c6834f, delta 56af4fbd, runner c3ef682f, ZIP
a7afd57a), self-check and 8/8 host simulation PASS. Status B4-R01 FIXED_PENDING_RUNTIME_REVIEW;
Q01 stays B4_NEEDS_REVISION; B5 not started. Next: Codex review, then the user's Studio run, then a
focused closure review. See evidence/notes/PHASE_B_B4_R01_FIX_EVIDENCE_20261015.md. No staging,
commit, push or deploy.

## B4-R01 code/package review —2026-10-15 (Codex)

PASS_CODE_AND_PACKAGE_REVIEW; B4-R01 FIXED_PENDING_RUNTIME_REVIEW, B4notclosed/B5notstarted.
18B4unitPASS, independent tiedtimestamp/multipledeferredpages/restoredscopes/all-deferredprobePASS,
SQLcompile/mapping4PASS, fixture20PASS/215checks/d17f58a3digest/optionalHTTPNOT_RUN1.
Sixdeclaredchangesonly;32localhashesf1c6834f,delta56af4fbd,runnerc3ef682f,ZIPa7afd57a verified.
Actualcollection104cases; PG/Redis64casesNOT_RUN. Last-reportedStudio is444cfead, notlocalf1c6834f.
User runs reviewedpackage per evidence/local/claude/prompts/B4_R01_STUDIO_RUN_20261015.md,
supplies output USER_REPORTED_REMOTE, then focusedclosurebeforeB5. No repeatedfix/RT01rerun.
LocalPhaseA skip is missingPillow per raw receipt, not POSIX-only. Top/bootstrap/localhandover
corrected to avoid restarting pre-fix work. Sameapproval/cards14/WIP1/fullDONE0. Review preserved
backend/packages/approvals/approvedplans; no installs/services/provider/staging/commit/push/deploy.
Review: evidence/notes/PHASE_B_B4_R01_CODEX_FIX_REVIEW_20261015.md, matchingmetric; ignoredreceipts local/b4r01-codex-review-20261015/.

## B4 closure and B5 handoff —2026-10-15 (Codex)

B4 CLOSED_REVIEW_PASS, B4-R01 CLOSED_B4_SCOPE, RT01closure retained. User fullStudio log
run2026-10-15T13:26:49Z exact32manifestf1c6834f/delta56af4fbd:104B2–B4PASS/0skip,
224PhaseAPASS/0skip, all exits0. Fixture20PASS/215checks/d17f58a3digest optionalHTTPNOT_RUN1.
USER_REPORTED_REMOTE; actualPGregressions now pass on reviewedsource. Concise104allpass/file11cases
covers2newPGtests, no extra verbose-output gate. Independent source/package/binding closurePASS.
ACTIVEQ01/B5_READY_FOR_IMPLEMENTATION, B5codeNOT_STARTED. Claude B5only via evidence/local/claude/prompts/CLAUDE_PHASE_B_B5_IMPLEMENTATION_PROMPT.md; original
PhaseBrev3approval applies, no repeatapproval/card/B4/environmentsetup. Local/Studio bothf1c6834f.
B5code/self-review/package thenCodexreview/userStudio/closurebeforeB6. Same14cards/WIP1/fullDONE0,
OwnerFenceASSUMED_CONTRACT/realB12deferred. Currentproof notes/PHASE_B_B4_CLOSURE_REVIEW_20261015.md and matchingmetric;
ignored rawlog/preclosuredocs/protected520pathchecks local/b4-closure-20261015/.
Closure changed docs/evidence/handover only, notbackend/tests/fixtures/packages/approvedplans/
approvals/index. No install/service/provider/stage/commit/push/deploy; B5 implementation notperformed.

## B5 implementation —2026-10-15 (Claude)

Implemented the approved B5 under the existing Phase B rev3 approval:
- **Δ8/Δ14.** HMAC attempt-bound worker capability (wcap.v1, 40 s fixture TTL, multi-key verify)
  and `_require_worker(token, job, attempt)` with service-side expiry. `DispatchWorker` runs
  start -> progress -> fake provider -> completion. RQ `receive_dispatch` never raises;
  `RedactingSimpleWorker` and the log redaction filter keep tokens out of log records.
- **Δ9/Δ15.** Job-changing completions commit the mutation, authoritative receipt, audit intent and
  owned quarantine intents together. Unchanged-job verdicts commit an audit-only incident before
  answering; a failed incident commit is a 503. Event ids are deterministic. After commit each
  intent is delivered once, then a leased `deliver_side_effects` pass delivers again; sinks
  deduplicate by event id.
- **Δ10.** Atomic notices: lock all matches, cancel them with audit intents, record `COMPLETE`;
  more than 100 matches fail typed.
- **Δ12.** Fake/SQL/fixture parity and caller updates. Fixture digest d17f58a3 unchanged.

Local results: Phase A 223/1 skip; B2–B5 89 passed / 94 PG-Redis skipped (NOT_RUN); 10/10 mutation
probes covered; lint, types and validators PASS. Package b5: 25-file delta 671a8617, 43-file
manifest c7492097, runner e7813419, ZIP 9475fe27; self-check and 8/8 host simulation PASS.

Status: B5_CODE_COMPLETE — PENDING_CODEX_REVIEW. Next: Codex review, the user's Studio run, then a
focused closure review before B6. See evidence/notes/PHASE_B_B5_IMPLEMENTATION_EVIDENCE_20261015.md. No staging, commit, push or deploy.

## B5 independent review —2026-10-15 (Codex)

NEEDS_REVISION, twoP2B5-R01/R02OPEN, ACTIVEQ01/B5_NEEDS_REVISION. R01:50failingoldauditrows
reclaimedonrepeat, pendingquarantinehealthysink0calls/3passes; currentservice/fakeproof reproduced,
SQLORDERBY/LIMIT/release independentlyconfirms. R02:malformednonalphabetMACencodingstillverifies,
actualworkercompletes, LogRecordfilterkeepsacceptedtoken; noHMACforgery/scopeescalationclaimed.
24capability/worker+25effects/noticesunitPASS andfixture20/215/d17baseline do not cover these cases.
SQLcompile5PASS; B5PGRedis30newNOT_RUN, no remoteexecution. Package43hashes/25delta/4ZIPvalid,
but do notrun current9475ZIP asnextacceptance. Localc7492097 != last-reportedStudiof1c6834f.
Claude fixes onlyR01/R02 per evidence/local/claude/prompts/CLAUDE_PHASE_B_B5_FIX_PROMPT.md; newpackage startsfromStudiof1c, thenreview/runtime/closure
beforeB6. B2/B3/B4closed, sameapproval/cards14/WIP1/fullDONE0. Root updateddocskipreason toPillow,
notPOSIX-only. Optionalrealworkerduplicateassertstrengthening not a thirdfinding/card/gate.
Review notes/PHASE_B_B5_CODEX_REVIEW_20261015.md+matchingmetric; probes/rawreport/protected535paths local/b5-codex-review-20261015/.
No source/package/approval/plan/index changes byreview, installs/services/provider/stage/commit/push/deploy.

## B5 fix01 (B5-R01/R02) —2026-10-15 (Claude)

Fixed only the two Codex findings under the existing approval:
- **R01.** `deliver_side_effects` is a per-invocation keyset traversal over all undelivered
  side-effect rows. Failing rows are released and passed over, so they never hide later
  healthy-sink rows; each row is tried at most once per invocation, so the call is finite.
- **R02.** The capability is checked as a whole-token shape with strict canonical base64url
  (non-alphabet characters, padding, non-canonical bits and trailing junk are rejected) before
  the MAC. Redaction covers malformed forms, every non-standard extra and rendered objects.

Probes: R01 before `[0,0,0]` (0 quarantine calls), after `[1,0,0]`. R02 before: the malformed
token was accepted, survived the filter and reached `succeeded`; after: rejected and job
`queued`. 5 new unit regressions fail on c7492097 and pass on the fix. The new SQL regression is
NOT_RUN locally. package b5fix01: delta c7a2d408 (25 files from f1c6834f), 43-file manifest 831147fa, runner f5a3cbd6, ZIP fa06d879.

Status FIXED_PENDING_REVIEW; Q01 B5_NEEDS_REVISION until review, Studio and closure. See
evidence/notes/PHASE_B_B5_FIX01_EVIDENCE_20261015.md. No staging, commit, push or deploy.


## B5 fix02 Codex takeover and current handoff —2026-10-15

User directive, preserved verbatim as executor authority (not a new approval):
> :)))) tạm thời bạn làm đi tí bàn giao tóm tắt lại cho claude vì nó làm tới đây thì hết token nè

B5-R01: fair keyset traversal passes failed sinks and captures the initial pending side-effect count as a finite row budget. At most that many claims/attempts occur per invocation; each claimed row is passed once, failures are released, and continuing arrivals cannot extend the budget. This is not a fixed-membership snapshot or wall-clock deadline; under concurrency new arrivals may consume the remaining budget. SQL/fake parity, generation leases, sink event-id dedup and dispatch bookkeeping stay intact. B5-R02: strict canonical whole-token acceptance retained; log messages are interpolated before scrubbing and arguments cleared; nested mapping keys and values are scrubbed. These are bounded corrections to the existing two findings, not new cards or architecture.

Direct local: B2-B5 97 passed / 96 PostgreSQL/Redis skipped (NOT_RUN); 57 B5 unit cases. Phase A 223 passed / 1 Pillow skip. Expected Studio: 193 B2-B5 passed / 0 skipped and 224 Phase A passed / 0 skipped; these are expected counts, not reported results.
Last reported Studio remains closed B4 manifest f1c6834f41dc798fe4475509b7d4b9c8c578ebfd15f34ff07f72f2d4bf24aeb4: 104 B2-B4 + 224 Phase A passed / 0 skipped, all exits 0, 2026-10-15T13:26:49Z, USER_REPORTED_REMOTE. No B5 runtime has been reported.

Current Q01/B5_FIXED_PENDING_RUNTIME_REVIEW; both findings FIXED_PENDING_RUNTIME_REVIEW. Codex finished the bounded
corrections and reviewed fix02 source/package; user Studio run is next. B1-B4 remain closed; B6 NOT_STARTED. Same Phase B revision 3 approval, 14 cards / WIP 1 / full-card DONE 0 / parent BE2-01 IN_PROGRESS. OwnerFence remains ASSUMED_CONTRACT; real B-12 integration deferred. No other card/provider/live router/BE1-owned writes/production/FEAT-018/Wan, install/service recreation/staging/commit/push/deploy.
Review evidence/notes/PHASE_B_B5_FIX02_CODEX_REVIEW_20261015.md; concise ignored handover evidence/local/claude/handover/CLAUDE_B5_CODEX_HANDOVER_20261015.md.

## Claude reset handover —2026-10-16

User requested a concrete summary and steps after Claude reset. Prepared local evidence/local/claude/handover/CLAUDE_RESET_HANDOVER_B5_TO_B6_20261016.md:
step 1 read-only rehydration; step 2 separate unchanged approved B6 implementation prompt.
Draft text does not start B6, write approval or change B5 closure. B6 remains NOT_STARTED.

## Agreed task-branch workflow —2026-10-16

owner-branch-workflow-20261016: Owner confirmed: finish one BE2 card, review and integrate it into dev, then create the next task branch from updated dev. One branch per card; B1-B6 remain on the existing BE2-01 branch. Create task branches when needed, not all fourteen upfront. Keep per-card plans/approvals/evidence and the existing dependency order. Current branch feature/be2-01-ai-job-foundation stays unchanged while Claude handles the B6 handoff. This workflow decision performs no branch/commit/push/merge operation and does not authorize other-card implementation.

## B6 implementation —2026-10-16 (Claude)

Implemented the approved B6 under the existing Phase B rev3 approval. B6 adds three files only;
the 43 fix03 files are unchanged.
- **Durable conformance runner** (`src/run_durable_conformance.py`). Phase A A-01..A-20 are mapped
  one by one. A-03..A-17 run on the real SQL adapter (a fresh database cloned from a migrated
  template per harness) with real Redis/RQ, HMAC and the ASSUMED_CONTRACT owner fixture.
  A-02/A-19/A-20 are contract-only, A-18 is deferred to BE2-14, and the HTTP surface is optional.
  The §7.1 crash windows W01..W12 and B-01..B-12 come from the same run's JUnit, the Phase A JUnit
  and the fixture report. B-12 is HANDOFF. Exit codes: 1 = FAIL, 2 = required NOT_RUN. There is no
  fake fallback.
- **B-01 restart regressions** (`test_restart_recovery.py`) with real process kills: before
  create commit, after commits (row checksum identical, then publish and delivery on restart),
  and after start (policy retry).
- **Offline runner-logic tests.**

Local results: 103 passed / 99 PG-Redis skipped (NOT_RUN); Phase A 223/1; fixture d17f58a3; the
durable runner exits 2 locally, as designed. package b6 (additive 3-file delta f34d8b1a from fix03 3930046b -> 46-file manifest 3940e529, runner aa9cc843, ZIP 5c2e4641); self-check and 9/9 host simulation PASS.

Status B6_CODE_COMPLETE — PENDING_CODEX_REVIEW. See evidence/notes/PHASE_B_B6_CONFORMANCE_EVIDENCE_20261016.md and evidence/notes/PHASE_B_B6_HANDOFF_20261016.md. No
staging, commit, push or deploy.

## B6 Studio run 1 and B6-fix01 —2026-10-16 (Claude)

- **Run 1 result.** B6 Studio run 1 (USER_REPORTED_REMOTE, 2026-10-15T18:19:36Z = 2026-10-16 01:19:36 Asia/Saigon) FAILED: B2–B6 201 passed / 1 failed / 0 skipped; Phase A 224 / 0 skipped; fixture 20 PASS / 215 (d17f58a3); durable runner exit 1 (A-01, A-03..A-17 and A-17-http PASS, 127 checks / 0 failed; FAIL only W02, W08, B-01, B-06); RUNNER_RESULT=FAIL.
- **Cause.** B6-RT01: the crash child in test_restart_recovery.py sent the Attempt object instead of attempt_id, so the restart lookup raised psycopg 'cannot adapt type Attempt'; all four FAIL rows map to that one test. The assertions before line 156 passed: child exit 23, the checksum of every
  ai_jobs row equal after restart, and the job blocked_unsafe at revision ≥ 3. The durable
  scenarios themselves had no failed check.
- **Fix.** Line 136 now sends `attempt.attempt_id`. The rest of the test (lines 142–173) was
  re-reviewed statically. No product code, runner or other test changed.
- **Local checks.** ruff/mypy 0; B2–B6 103 passed / 99 PG-Redis skipped (NOT_RUN); validators 0.
- **Package.** package b6fix01 (one-line delta 11e238c7 from the Studio B6 snapshot 3940e529 -> 46-file manifest 90724453, runner 55695aef, ZIP e813a48b). It is accepted only on the exact Studio B6 snapshot, or as a verify-only
  retry of the fixed manifest. Self-check and 9/9 host simulation PASS.

Status B6_FIX01_CODE_COMPLETE — PENDING_CODEX_REVIEW. No staging, commit, push or deploy.

## B6-fix01 pre-run review —2026-10-16 (Claude)

Codex ran out of tokens. The user directed Claude to do the pre-run review ("codex hết token r phần này bạn làm lun đi xong tôi đi ngủ").
- **Verdict.** pre-run review PASS as AUTHOR SELF-REVIEW (Claude; Codex out of tokens, user-directed), not an independent review; package audit and no-service restart-flow probe PASS.
- **Package audit.** Run along a path different from the builder:
  - Studio's test bytes were recovered from the shipped b6 delta, and the fixed file differs from
    them in line 136 only;
  - the reverse patch gives 3940e529 and the forward patch gives 90724453;
  - the runner differs from b6 only in names, pins and state labels;
  - all ZIP members are byte-identical.
- **Restart-flow probe** (no services):
  - the fixed payload adapts in psycopg, and the run-1 payload reproduces the Studio error;
  - on the in-memory store, the post-restart flow yields exactly the counts the test asserts.
- **Limits.** This is not independent review. The test's lines 157–173 have not run on
  PostgreSQL. The B6 closure review must be independent.

Evidence: evidence/notes/PHASE_B_B6_CONFORMANCE_EVIDENCE_20261016.md §10.

## B6-fix01 Studio run —2026-10-16 (Claude recording)

- **Result.** B6-fix01 Studio run (USER_REPORTED_REMOTE, 2026-10-15T18:49:30Z = 2026-10-16 01:49:30 Asia/Saigon) PASSED: source b6_snapshot 3940e529 -> 90724453 (46 files verified); B2–B6 202 passed / 0 failed / 0 skipped (all 3 restart tests and the 6 B6 unit tests included); Phase A 224 / 0 skipped; fixture 20 PASS / 215 (d17f58a3, optional HTTP NOT_RUN 1); durable runner exit 0 (required 39/39 PASS, 127 checks / 0 failed; W01..W12 and B-01..B-11 PASS; A-17-http PASS; A-18 DEFERRED; A-02/A-19/A-20 NOT_APPLICABLE; B-12 HANDOFF); every suite/log/outer/Studio exit 0, RUNNER_RESULT=PASS.
- **Timing.** The run started while the author pre-run review was finishing:
  - the package audit had passed at 01:46;
  - the restart probe ran at 01:49:38, and the review record was written at about 01:50:46;
  - these times are approximate, compared across the Studio and Windows clocks;
  - the run used exactly the reviewed bytes (all pins match).
- **Studio.** The user stopped the Studio after the run (to avoid charges), so its Docker services, network and venv volume may be gone; any later runtime starts with an inventory and recreates nothing without the owner-approved procedure.
- **Observation (non-blocking).** `backend/pyproject.toml` sets `addopts = "-q"`, which cancels the
  runner's `-v`. As a result the summary's per-test restart/B6 lines were empty in both runs. The
  per-test results are in the JUnit, which the durable runner consumed.

Status B6_RUNTIME_PASS — PENDING_INDEPENDENT_CLOSURE_REVIEW. B6 is not closed, and BE2-01 is not
DONE. No staging, commit, push or deploy.

## B6 independent closure review —2026-10-16 (separate Claude review session)

- **Provenance.** Independent closure review by a separate Claude review session: it did not write
  B6, fix01 or the pre-run review, and it judged from code, package and evidence rather than the
  author's conclusions. It is session-separate, not model-separate.
- **Verdict.** **CLOSE_WITH_NOTES**: B6 closed at component scope on manifest 90724453 (re-verified
  46/46 OK from the worktree root); Phase B B1–B6 component-closed; B-12 HANDOFF, never PASS.
- **Findings** (0 H / 1 M / 4 L):
  - B6-CR01 (M): the durable runner alone is not a self-sufficient gate. Unmapped or missing tests,
    any Phase A JUnit, a 0-check fixture report and an empty manifest still pass. The b6fix01 run is
    valid because the package guards compensate, so records cite RUNNER_RESULT, never
    `durable_runner_exit` alone. The owner chooses: keep as a limitation, or harden (new package and
    Studio run).
  - B6-CR02..CR05 (L): mapping traceability (B-06(d) test unmapped; W11 differs from B1 row 11); the
    run-1 report is condensed although labelled verbatim; the runner usage text; this file's stale
    head (now refreshed).
- **Other records.** B6-RT01 CLOSED. Codex's B6 review record is INCONSISTENT and not counted as a
  Codex PASS. The pre-run review stays AUTHOR_SELF_REVIEW.
- **Next.** The owner records the B6 closure decision; then the BE2-01 card review and integration
  into dev per decision 116.

BE2-01 IN_PROGRESS, not DONE. No code, test, package, approval, plan, DECISIONS or metrics change;
no staging, commit, push or deploy. Evidence: evidence/notes/PHASE_B_B6_CLOSURE_REVIEW_20261016.md.


## Codex CR01 pre-commit snapshot review —2026-10-16

Review of runner 87f0961f / B6 unit f07a1f4c: NEEDS_REVISION for the CR01 hardening snapshot. Missing parametrized testcase [120] while retaining [81] still yields G-01 PASS (211 of 212 collected B2-B6 cases). Compare full collected testcase identities, including parameter IDs; add focused regressions. Direct local B6 units16 PASS, ruff/mypy/harness/architecture/security/diff PASS; PostgreSQL/Redis NOT_RUN locally. The older 90724453 runtime and publication dry run do not cover these two changed files. This is a source-bound reviewer observation, not an owner decision or a new task/approval. See evidence/notes/PHASE_B_B6_CR01_CODEX_PRECOMMIT_REVIEW_20261016.md. Later source requires rechecking. Same approved Phase B scope; BE2-01 IN_PROGRESS, B-12 HANDOFF. No source/package/Git mutation by this review.

## B6-CR01 hardening —2026-10-16 (Claude)

Person 2 chose to harden B6-CR01 rather than keep it as a limitation ("Chọn làm cứng B6-CR01, giới hạn trong runner và test liên quan … Giữ cặp note/metrics B4-RT01 trong repo vì các evidence khác đang tham chiếu tới chúng.").
- **Change** (runner and its tests only): the durable runner now gates itself: G-01/G-02 aggregate every JUnit case of the B2-B6 and Phase A suites against the test ids pytest collects from the running tree, parameter variants included (failure or a case outside the inventory = FAIL, missing or skipped case = NOT_RUN); W/B patterns must cover every inventory test they name; G-03 needs the complete fixture report (A-01..A-20 PASS, checks > 0, digest); G-04 needs a pinned, well-formed, non-empty manifest that matches the tree and lists every Phase B surface file. A-01 now relies on G-04, and the package runner
  passes `--manifest-sha256`.
- **Regressions:** 11 new offline tests (one for the Codex parameter-variant P2) reproduce the closure review probes, namely an unmapped
  failing test, missing or skipped tests, a foreign case, an arbitrary Phase A JUnit, an
  incomplete fixture report, and empty/unpinned/incomplete/tampered/malformed manifests.
- **Checks.** Local: ruff/mypy 0; B6 unit 17 passed (11 new CR01 regressions for the review probes P1-P4/P7 and more); B2-B6 114 passed / 99 PG-Redis skipped (NOT_RUN); Phase A 223 / 1 Pillow skip; fixture d17f58a3 unchanged; hardened runner on real local evidence exit 2 (G-03/G-04 PASS, G-01/G-02 and scenarios NOT_RUN, no FAIL); validators 0.
- **Package.** package b6cr01 (two-file delta 5e1f6012 from the Studio B6-fix01 snapshot 90724453 -> 46-file manifest a75841e0, runner 5f8858d7, ZIP d0b9f27b).

Status: B6-CR01 FIXED_PENDING_RUNTIME_REVIEW. The B4-RT01 note/metrics stay published, so the
publication plan now has 123 paths. No staging, commit, push or merge.


## Codex focused CR01 re-review —2026-10-16

PASS_LOCAL_PENDING_FINAL_PACKAGE_AND_RUNTIME on runner d42d697c and B6 unit b1d3bced. The earlier parameter-variant P2 is resolved: heldout B2-B6 and Phase A missing variants produce NOT_RUN; unmapped failure plus a missing variant produces FAIL/exit1; collection error fails closed. Direct local21 B6 units PASS, ruff/mypy PASS. Source hashes stayed stable through the probes. See evidence/notes/PHASE_B_B6_CR01_CODEX_PRECOMMIT_REVIEW_20261016.md (latest addendum) and ignored evidence/local/b6-cr01-codex-rereview-20261016/. Earlier ZIP d0b9f27b/a75841e0 package audit PASS applies to its immutable bytes; author edits advanced source beyond it. Final source-bound package/Studio result and refreshed publication dry run remain required. Runtime NOT_RUN locally; same approved B6 scope, BE2-01 IN_PROGRESS, B-12 HANDOFF. No code/approval/Git operation by this review.

## B6-CR01 r2 —2026-10-16 (Claude)

- **Source.** The Codex pre-commit review (`notes/PHASE_B_B6_CR01_CODEX_PRECOMMIT_REVIEW_20261016.md`) of runner 87f0961f found that a missing
  parameter variant still passed G-01. The correction stays within the runner and its unit tests.
- **Fix.** case identities are the full pytest ids (file path relative to backend/, class parts, parameter id) taken from `pytest --collect-only` of the running tree and normalised identically from JUnit; collection is all-or-nothing (exit code, pytest's own total, no case outside the suite files, every file collected).
- **New regressions.** The PostgreSQL `[120]` case missing while `[81]` ran; a real Phase A variant
  missing; a failure plus a missing case (exit 1); identity normalisation; and a broken collection
  that never yields a partial inventory.
- **Proof.** Scratch before/after on the same synthetic JUnit from real collection: the reviewed bytes 87f0961f still report G-01/G-02 PASS with `[120]` or a Phase A variant missing; the current runner reports NOT_RUN for both, PASS when complete and FAIL (exit 1) for a failure plus a missing case.
- **Checks.** Local: ruff/mypy 0; B6 unit 21 passed; B2-B6 118 passed / 99 PG-Redis skipped (NOT_RUN); Phase A 223 / 1 Pillow skip; fixture d17f58a3; collected identities equal the real JUnit identities (217/217 B2-B6, 224/224 Phase A); runner on real local evidence exit 2 with G-03/G-04 PASS and no FAIL; validators 0.
- **Package.** package b6cr01r2 (delta 9d9146c6 from the Studio B6-fix01 snapshot 90724453 -> 46-file manifest cb527d7f, runner d027d05c, ZIP 3a9d6ef2); it supersedes the never-run b6cr01 package (ZIP d0b9f27b, kept unchanged).
- **Correction to an earlier record.** The first b6cr01 build (ZIP 575aa8f4) was rebuilt in place
  to d0b9f27b in the previous turn. Neither was ever run on Studio.

r2 has no runtime result yet. CR01 is not closed. No staging, commit, push or merge.
