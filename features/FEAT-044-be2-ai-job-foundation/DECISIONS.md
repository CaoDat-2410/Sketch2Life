# BE2 planning decisions — 2026-10-14

## Claude D3 rereview 4 — completion-time resource gate — 2026-10-21

D3 remains the direct owner direction. Claude closed the original rereview-3 P2 findings in draft and found NEW-1: completion-time BUDGET_EXCEEDED falls through the generic _decide_completion cancel/quarantine branch after provider work. D3 only resolved dispatch/start/retry. See FEAT-057 report SHA256 92BE229378A2DE06BAEED1FC6F675EA15FED338892A002A833F81F6972B44C12.

Foundation scope Rev7, budget CR Rev2 and stale CR Rev2 record completion-time resource denial as an unresolved owner/card-contract gate; they do not treat it as consent/kill cancellation or silently extend C1-A. A D4 ballot is prepared. Its recommended option is not owner-approved. The drafts clarify validation order, typed descriptor availability, stable journal operation identity and temporary/audit interpretation.

No source/test/schema/approval changed. D3 remains selected; implementation, supplemental S/F/schema approval, budget parameters, BE1 adoption and D4 remain open.


## Owner D3: durable QUEUED hold and atomic B-stale - 2026-10-21

Direct owner C1-A/C2-A conditions are recorded in FEAT-057 evidence/notes/CROSS_LANE_UOW_OWNER_DECISION_D3_20261021.md, SHA256 C1799417AFD2DDB989D6C888A8B3F9702D4A6B4DC2A8B90637DBD6E11C3AE54C. D1/D2 remain applicable.

BE2-01 owns durable hold metadata with both job/run QUEUED, no budget lifecycle state. Change all three budget-denial branches (_dispatch_one, start_attempt, retry_job) through the joint BE2-01/14 CR; consent/kill still cancel. Exclude hold from claim/ack/dispatch-loss/watchdog/retry allowance; resume rechecks eligibility and reservation. A due/otherwise eligible retry creating exactly one normal next attempt plus queued participant/hold is a review candidate, not a newly adopted implementation contract. Endpoints are RESUMED or legitimately CLOSED. Numeric bounds/deadline action and budget terms stay pending; schema/new-migration CR is separate and published migrations stay unchanged.

B-stale is BE2-01's authoritative SUCCEEDED/STALE receipt/result-refs commit, paired with video terminal stale/no artifact/no ready state and descriptor-proven cleanup intent in the same transaction. BE1 artifacts-owner adoption for owned job/attempt refs, a fixed reason, deterministic identity and accepted-reference protection remains pending. Unmappable descriptors fail closed. All completion classes/state pairs and residual P3 obligations are specified in scope Rev6 and the CRs.

Latest drafts: plan/CROSS_LANE_FOUNDATION_UOW_SCOPE_REV6_DRAFT_20261021.md; plan/CROSS_LANE_BUDGET_DEFERRAL_CR_DRAFT_20261021.md; plan/CROSS_LANE_BUDGET_DEFERRAL_SCHEMA_CR_DRAFT_20261021.md; plan/CROSS_LANE_STALE_FINALIZATION_CR_DRAFT_20261021.md. D3 is design authority only; independent review and separate supplemental S/F/schema approvals are still required. Existing exact-hash approvals do not cover these expanded paths. No code, tests, migrations or official approvals changed.


## Owner D1: paired lifecycle UoW direction — 2026-10-21

The owner selected model A for the cross-lane BE2-01/08 lifecycle. BE2-01 owns
and opens the foundation UoW for A/S/B/F, including reconciler timeout/retry/
cancel and outbox-driven job transitions; BE2-08 is a non-committing participant
limited to its own video rows. Rejected finalization writes quarantine/cleanup
intent through the existing foundation path in a separate reject commit. A
finalization rollback is only for infrastructure error and requires recovery.
The selected scope lock order is job → video run → fence rows by stable key;
Claude must verify feasibility against the actual lock paths.

This is design direction only. It does not expand the existing Phase B or typed-
dispatch approval, and is not approval to change source, schema, tests, status or
acceptance. S/F require independent review and separate supplemental approval.
The scope successor is
`plan/CROSS_LANE_FOUNDATION_UOW_SCOPE_REV3_DRAFT_20261021.md`; owner receipt is
in FEAT-057 `evidence/notes/CROSS_LANE_UOW_OWNER_DECISION_D1_20261021.md`.
The current FEAT-057 slice plan revision 4 still needs an explicit successor or
erratum disposition. No runtime, provider, Modal, Lightning or database work is
authorized.

## Supplemental typed dispatch implementation — 2026-10-21

Implemented the owner-approved BE2-01 route within the frozen execution
manifest: explicitly configured BE2-08 type to registered worker; original
envelope forwarded unchanged; existing `sketch_assistance` provider route
preserved; unknown types rejected before provider/start. Focused offline tests
79/79, Ruff and strict mypy pass. This does not prove X09-08 composition, change
Phase B scope, or close BE2-01 acceptance/runtime gates. Evidence:
`evidence/notes/CROSS_LANE_TYPED_DISPATCH_IMPLEMENTATION_20261021.md`.

## FEAT-057 implementation-scope addendum — 2026-10-21

- Approved addendum: plan/CROSS_LANE_BE2_01_SCOPE_DRAFT_20261021.md
- Approval record: approvals/PHASE_B_TASK_APPROVAL.md
- Proposed scope is only a typed route for the adopted BE2-08 job type at the existing foundation dispatch boundary. It does not change the approved Phase B scope, envelope/schema, or provider behavior.
- Owner approved the exact scope SHA256 AD1BA2706655CD040ACBBBF508577F79A41F5D5B3EF57D1437DA4C7F7F185DBD. The verbatim approval is recorded in approvals/PHASE_B_TASK_APPROVAL.md.
- The minimal execution file subset was recorded before edits in the official approval. The bounded dispatch change is separately documented above; card status/acceptance are unchanged.

## FEAT-057 cross-card owner response — 2026-10-21

The user confirmed they own the affected cards and approved the G0 proposal
with `Chốt theo đề xuất`. For BE2-01, B2–B4 are `ADOPT_WITH_CHANGES`: separate
submission/finalizer atomic boundaries; authoritative replay/lost-ack and
late-attempt winner semantics; and a typed BE2-08 route with explicit immutable
subject/session/source-pin/idempotency mapping. Provider work remains between
the two transactions; unknown job types fail closed. See FEAT-057's
`evidence/notes/G0_CARD_OWNER_DECISION_BALLOT_20261021.md`.

This adopts contract direction only; it does not approve new foundation
source/schema changes or expand the existing Phase B approval. BE2-01 status and
acceptance are unchanged.

1. **Planning authority only.** The direct user request authorizes a concrete plan. Runtime remains NOT_STARTED; approval is the generated AWAITING_APPROVAL placeholder, unchanged. No authority is inferred from branch name or FEAT-040 documentation DONE.
2. **Preserve worktree boundaries.** Plan is authored in the existing BE2 worktree. Root branch and its unrelated changes stay intact; pre-existing Android Gradle wrapper edit in this worktree is outside scope.
3. **Two BE2-01 delivery gates.** Phase A is independent fake/contract code; Phase B owns actual durable jobs/outbox/queue/CAS after separate decisions/approval. Both remain P3 responsibility, as FEAT-040 requires.
4. **Source semantics first.** SRS DATA-25 states and disposition/progress axes remain separate. Job success does not approve media or complete sessions; reads/cache/completion recheck current authority.
5. **Parallel paths after foundation.** Vision, knowledge and publication can proceed independently by contract. Shared DATA-24 and ProviderCopyLifecycle candidates are prepared early with their original schema owners; no new live dependency cycle.
6. **No stack/numeric-policy freeze.** Named fixtures retain PROPOSED policy values. FastAPI/React Native/Android are confirmed; other choices require applicable ADR and feature approval. This plan creates no cross-feature ADR adoption.
7. **Verification scope.** Documentation review and existing repository checks only in this change. No component test pass/real inference/capacity/deletion claim. Future implementation checks and missing dependencies are labelled separately.

Sources: `docs/adr/ADR-0015-four-person-role-and-integration-allocation.md`, FEAT-040 current backlog, canonical SRS v3.1. Audit: `evidence/notes/SOURCE_AUDIT.md`; validation/review receipts: feature evidence index.

## Claude handoff amendment — 2026-10-14

8. **Executor:** user assigns BE2 work to Claude. This is implementation-agent preference, not reassignment of P1/P2/P3/P4 ownership. Codex prepares handoff/review documents; no backend code is authored here.
9. **Approval boundary:** detailed instructions and agent assignment alone do not identify exact Phase A approval. Provide a ready-to-send approval message separately from the implementation prompt; retain current AWAITING_APPROVAL placeholder. Once valid approval exists, the prompt instructs Claude to proceed without repeated routine confirmation.
10. **Implementation clarifications:** SRS B22.1 command key includes organization/principal/contract/target/key; semantic dedup and receipt disclosure are separate. Fake dependencies only in isolated fixture/test app; no live auth downgrade. These clarify the unapproved plan, without stack/schema adoption.
11. **Dispatch:** Claude CLI presence is observed; authentication/actual execution remains untested. Prompt delivery is ready for manual dispatch; optional user dispatch preference can steer subsequent execution.

## Phase A implementation decisions — 2026-10-14 (Claude, local fixture proposals)

12. **Approval recorded before code.** User's explicit Phase A revision 1 approval recorded
    verbatim; plan/status moved to IN_PROGRESS. Phase B, BE2-02..14, providers, installs and
    commit/push/deploy remain excluded.
13. **Candidate spec first.** Fingerprint fields, receipt identities, revision/attempt events,
    completion disposition matrix, fake atomic boundary, DATA-25 nullability/timezone and role
    allowlists are in `plan/PHASE_A_CANDIDATE_SPEC.md`; all PROPOSED, none adopted.
14. **Context drift = `succeeded` + `stale`.** Keeps DATA-25 states closed; result kept for
    lineage, never projected. Revocation at completion = `cancelled` + `rejected`.
15. **Malformed/non-retryable failures exhaust immediately** (VIDEO_RETRY_BUDGET: schema/policy
    errors not auto-retried). Unsafe output = `blocked_unsafe`.
16. **Cancel needs If-Match** (`expected_job_revision`) per B22.1; owner notices bypass it and are
    idempotent by notice id.
17. **ETag includes a projection variant** so consent/grant changes cannot be served from a 304.
    Missing and inaccessible jobs share `404 RESOURCE_NOT_FOUND`.
18. **Fixture app isolation.** CMD-44 router is only mounted by `interfaces/http/ai_jobs_fixture_app.py`
    with synthetic `Fixture` tokens; `app.py` unchanged (AST test). No completion HTTP route.
19. **Existing environment reused, not installed.** Checks ran with the pre-existing
    `backend/.venv` (pytest/FastAPI/ruff/mypy present) with PYTHONPATH/MYPYPATH pinned to this
    worktree; the runner also runs on the default interpreter. Pillow is absent there, so the
    live-app route check skips (`REQUIRES_LIGHTNINGAI_TEST`).

## Independent implementation review — 2026-10-14 (Codex)

20. **Review before acceptance.** Existing test/runner receipts reproduce, but additional synthetic probes show Phase A defects. Review result NEEDS_REVISION, not component acceptance; approval remains Phase A revision 1 and full BE2-01 remains IN_PROGRESS.
21. **Fix ownership and scope.** Claude remains executor for fixes. R01–R11 in the implementation review record are corrections within approved Phase A behavior; no durable DB/provider/adoption scope is added. Review evidence and history are preserved; post-fix independent closure is separate from executor checks.

## BE2 roadmap control — 2026-10-14

22. **One routing entry.** User asks for full task analysis and a roadmap to follow against scope bloat. BE2_ROADMAP.md revision2 is the current local execution-order/scope-control document; tracker records actual active scope and gates. Source requirements/allocation and approved feature scope keep their own authority.
23. **One active implementation.** Claude is dispatched one card/checkpoint at a time. Default order: 01A closure → 01B → 12 → 14 → 02 → 03 → 04 → 05 → 06 → 07 → 08 → 09 → 10 → 11 → 13. This selected queue is not a new dependency graph or sprint/team allocation.
24. **Controlled waiting gates.** Missing DB/model decisions can permit specifically documented candidate-only/library substitutions with exact approval, remaining obligations and return slot; no silent jump or full-card fake DONE. Shared review/copy schemas do not force live dependency cycles.
25. **No new business scope.** Keep 14 cards/14 primary CMD/10 primary DATA. Checkpoints/findings are not additional business tasks. Requirement defects stay within owning card; enhancements go to a later change record and require an explicit scope decision. No speculative generic platforms, extra profiles or broad refactors.
26. **Preserve approved records.** Roadmap revision1 archived; no approved Phase A plan/approval bytes or source requirements changed. Runtime scope remains approved Phase A only. Roadmap adds workflow/documentation, not blanket implementation/model/cloud/publication authority.

## Q00 correction decisions — 2026-10-14 (Claude, local fixture proposals)

20. **Artifact lineage gate (R01).** Accept or quarantine an output only when the artifact port
    reports the job's organization and producer lineage = this job/attempt. Adds optional
    `producer_job_id`/`producer_attempt_id` to the candidate `ArtifactDescriptor` (P2 review).
21. **Semantic dedup bound to scope (R02).** Key adds target, purpose, session and sorted
    subjects; a scope change creates a separate job instead of a silent merge.
22. **Authoritative completion slot (R03).** Only job-changing completions occupy the immutable
    `(job, attempt)` slot; guard rejections are non-authoritative, audited, not stored.
23. **Worker outcome boundary (R04).** Unknown/malformed provider codes → PROVIDER_ERROR (hash
    only); malformed claims → non-authoritative MALFORMED_CLAIM; domain validates code format.
24. **Purge atomic boundary and replay (R05/R06).** Registry `scope_lock` (fake) serialises
    same-scope purges; replay returns that key's own immutable result.
25. **Contract tightening (R07/R08/R11).** String-only enum membership; refs only with
    succeeded+accepted; no disposition on non-terminal states; shared Child state rules.
26. **Dispatch recheck and poll-aware ETag (R09/R10).** Eligibility rechecked before enqueue;
    ETag variant includes `poll_after_ms`, retry wait rounded to whole seconds.
## Q00 independent closure review — 2026-10-14 (Codex)

Original fixes acknowledged with independent tests/repros. Overall review remains NEEDS_REVISION for R03a/R04a (direct fix follow-ups) and A18a (pre-existing gap in the already-required copy lifecycle invariant). They remain within Q00/Phase A, not new business cards/runtime scope. Original review/evidence, current approval/approved plan and routing retained. Codex only updated review records; Claude retains fixes. Evidence: evidence/notes/PHASE_A_Q00_CODEX_CLOSURE_REVIEW_20261014.md.

## Q00 follow-up decisions — 2026-10-14 (Claude, local fixture proposals)

27. **Temporary guard rejections do not touch artifacts (R03a).** `INVALID_STATE` and
    `INPUT_MISMATCH` keep the attempt completable, so they no longer quarantine; final outcomes
    still do. Admission rejects any ref reporting `quarantine_reason`, so quarantined bytes are
    never released by a later claim (no blind unquarantine).
28. **Type-checked worker codes (R04a).** Non-string `failure_code` → non-authoritative
    `MALFORMED_CLAIM` (hash-only audit); non-string ids → `400 MALFORMED_REQUEST`; fingerprints
    tolerate non-JSON values.
29. **Cancellation under the purge scope lock (A18a).** Reuses the existing fake atomic
    boundary; no new infrastructure.

## Final Q00 closure decision — 2026-10-14 (Codex)

30. **Corrections independently closed.** Final code review PASS at fake/contract scope; original11 and R03a/R04a/A18a CLOSED. No new finding or code-fix task is added in this reviewed scope. Review/history and executor before/after receipts retained.
31. **Acceptance gates retained.** Keep ACTIVE Q00 pending P1/P2/P4 adoption and the live-app route check needing Pillow or an explicit checkpoint deviation. Code PASS does not adopt candidate semantics or prove durable recovery/provider deletion. Phase B remains unapproved and needs separate plan/ADR/ports/approval; approved Phase A plan/approval unchanged. Evidence: evidence/notes/PHASE_A_Q00_FINAL_CODE_REVIEW_20261014.md.

## Q00 acceptance work order clarification — 2026-10-14

32. **Candidate handoff is bounded.** PLAN.md A9/A-20 requires cross-review/consumer pack. Owner may accept the Phase A candidate/fixture checkpoint and explicitly defer production adoption; this does not adopt production ports/policies/registry or remove Phase B prerequisites. Claude prepares the reviewable record and uses genuine decisions; no invented owner sign-off. Acceptance/environment gate remains pending.
33. **Skipped test evidence.** The exact live-app route test uses importorskip(PIL). Require actual 1 passed/0 skipped, not merely exit0. No installs under existing approval. New acceptance prompt confines the next Claude turn to docs/gate checks; Phase B planning and implementation remain later separate scopes.

## Q00 acceptance-gate decisions — 2026-10-14 (Claude, executor; no owner decision implied)

34. **No inferred sign-off.** Searched FEAT-044 records and project context; no consumer/owner
    adoption or acceptance decision exists. Gate record marks every decision
    PENDING_OWNER_DECISION with the specific question; reviewer agents are not owners.
35. **Live-route gate stays NOT_RUN.** Exact command ran in the reviewed venv (1 skipped). No
    existing interpreter combines pytest + FastAPI + Pillow; environment splicing, installs,
    setup and remote LightningAI runs (which would need the uncommitted reviewed source on a
    remote host) were not done. No deviation recorded because no owner decided one.

## Acceptance delivery review and planning preparation — 2026-10-14 (Codex)

36. **Review only current evidence.** Executor source hashes/anchors and actual skip were verified. Corrected three documentation statements to avoid implying Phase B capability needed for fixture acceptance, owner sign-off from runner A20, or hash-match needed to quarantine owned malformed output. Original code closure/approval retained; no new code task.
37. **Continue independent planning.** User asks to continue. Prepare Claude's Phase B plan/ADR/port-review prompt while Q00 decisions/environment wait; planning is reversible documentation and does not activate runtime code. Phase A/Phase B decision/approval gates remain explicit. Source scope stays14 cards; P3 implements, Codex plans/reviews.

## Phase B planning decisions — 2026-10-14 (Claude, proposals only)

36. **Plan, not authorisation.** Phase B plan rev 1 is PLANNED/AWAITING_APPROVAL; code needs Phase A
    disposition, independent plan review, a separate approval naming the revision, adopted ADR
    D1–D6, P2/P4 port answers and an authorised synthetic Linux environment.
37. **Stack proposal reuses existing candidates.** PostgreSQL + SQLAlchemy Core/psycopg + Alembic
    and Redis/RQ (ADR-0003, compose) are proposed for BE2 durable jobs only; PostgreSQL-only queue
    is the documented alternative. Not adopted.
38. **Scope fence.** BE2 owns schema `ai_jobs`; no BE1 tables, live router, provider inference or
    durable ProviderCopyLifecycle (BE2-14) in Phase B.

## Independent Phase B plan review — 2026-10-14 (Codex)

39. **Correct design before approval.** Rev1 review NEEDS_REVISION for PB-R01–PB-R06. Preserve six batches/14 cards and scoped SQL/outbox/queue/worker responsibilities; require current-owner fencing, exact uniqueness/rollback, queued recovery, attempt capability enforcement, durable incident audit and complete notice cancellation semantics before implementation. These are planned-scope corrections, not a new platform/provider/workstream.
40. **Revision remains documentation.** Claude prepares rev2 through evidence/local/claude/prompts/CLAUDE_PHASE_B_PLAN_REVISION_PROMPT.md; proposals remain PROPOSED and findings pending independent re-review. No approval/stack adoption/code from this review. Phase A code PASS retained; ACTIVE Q00 acceptance pending. Whole BE2-01 IN_PROGRESS.

## Phase B plan revision 2 decisions — 2026-10-15 (Claude, proposals only)

39. **Owner fence over job CAS (PB-R01).** Acceptance points hold P2-owned decision fences in the
    same DB transaction (D7, Q8); job CAS alone is not claimed to protect owner state. Fallback is
    weaker and needs plan amendment.
40. **Rollback-on-conflict creates (PB-R02).** Plain INSERT, full candidate rollback, fresh
    re-read; semantic identity is a canonical sha256 PK (NULL-safe).
41. **SQL owns redelivery (PB-R03).** RQ retries disabled; reconciler republishes the same
    attempt; no same-claim recovery after provider output.
42. **Attempt-bound capability, durable incidents, atomic notices (PB-R04–R06).** Typed
    `VerifiedCapability`; audit-only incident transaction with deterministic `event_id`; notices
    cancel all matches in one transaction with a named size guard.

## Focused Phase B revision2 closure — 2026-10-15 (Codex)

43. **Close original cases, bound follow-ups.** PB-R01–PB-R06 CLOSED_ORIGINAL_PLAN_CASE at design-review scope. Only PB-C01 queued transport-loss domain transition and PB-C02 explicit capability/quarantine-id carriers remain to list before implementation. Preserve chosen fence/SQL/recovery/audit/notice mechanisms and existing batches/acceptance IDs; do not add cards or unrelated review preferences.
44. **Keep evidence/adoption separate.** Source/hash/archive checks and static interface/guard analysis support plan review; no runtime PASS or owner sign-off. D1–D7/Q1–Q8/policy/env decisions remain proposed/pending. Claude prepares bounded rev3; ACTIVE Q00 and Phase B approval gates unchanged.

## Phase B plan revision 3 decisions — 2026-10-15 (Claude, proposals only)

43. **Queued dispatch loss is its own pure transition (PB-C01).** `record_dispatch_loss` is the
    only Phase B domain change; `record_failure` stays RUNNING-only; reconciler applies it under
    CAS against `start_attempt`.
44. **Explicit carriers (PB-C02).** Capability travels only in a transient
    `WorkerDispatchEnvelope`; quarantine uses `QuarantineIntent` whose stored `event_id` is resent
    unchanged on redelivery.

## Temporary publication selection — 2026-10-15

Direct user request authorizes provisional file triage:364 GitHub candidates,61 operator-local intermediate diagnostics and one separate Gradle change in the original426-file snapshot. evidence/notes/PUBLICATION_SELECTION_20261015.md records policy/original local hashes. Selected diagnostics stay at the same paths; source/test/runner/fixture/approved-plan/approval bytes are preserved. .gitignore hides only selected untracked diagnostics and feature-local operator reports. No stage/commit/push, new runtime scope or approval. Root branch's five unrelated changes are untouched. Actual validation/manifests live under evidence/local/publication-triage-20261015/.

## Final Phase B revision3 plan review — 2026-10-15 (Codex)

45. **Design corrections closed.** PB-C01/PB-C02 CLOSED; rev3 plan review PASS, six original closures retained. Preserve current six-batch/14-card design; future implementation validates exact acceptance rather than generating optional plan revisions. RQ structured-failure log suppression is part of existing B-05e/B-10c token-free logging, not a new task.
46. **Decisions are the next gate.** B1 prepares one record for G1/G3/G4/G5 and separate G2 approval. Review PASS does not sign for P2/P4, accept Phase A, adopt D1–D7 or prove runtime durability. Claude remains code executor after authorization; .gitignore local diagnostics and source/approval freeze retained.

## Phase B B1 decision record — 2026-10-15 (Claude, proposals only)

47. **One decision record, no inferred answers.** `plan/PHASE_B_DECISION_RECORD.md` is the single B1 record for
    G1–G5. Every open row is PENDING_OWNER_DECISION. Answers are recorded verbatim with record type
    (ROLE_OWNER_RECORD vs PROJECT_OWNER_DIRECTIVE); a project-owner answer to a role question is
    never relabelled as that role's sign-off. Alternatives (D3/D7 etc.) trigger plan amendment +
    focused review before G2, never quiet adoption.
48. **Fixture profile, not production.** `fixture.durable_jobs.v0` proposes test-only values for
    `DISPATCH_START_TIMEOUT`, `DISPATCH_MAX`, `NOTICE_ATOMIC_MAX`, capability slack, lease and RQ
    TTLs, reusing Phase A attempt/poll fixture policies. All PROPOSED; production values need a
    later versioned policy. Phase B approval, when given, goes in a separate approval file; Phase A
    `approvals/TASK_APPROVAL.md` stays unchanged.

## Scoped B1 record review — 2026-10-15 (Codex, no owner decisions)

49. **Consistent decision provenance.** G3-D7 and G4-Q8 use the same rule: genuine P2 role-owner
    record or explicit project-owner directive adopting/assigning the versioned component
    contract and ASSUMED_CONTRACT proof. A directive is never P2 concurrence or real adoption/
    integration evidence. All actual decisions remain pending; this clarification supplies none.
50. **Complete independent B1 preparation.** Draft seven proposed sequences/crash-window table
    now against preferred D3/D7. Adoption is required for B1 exit, not draft creation. No new
    plan revision/card/question set; Claude remains executor and code is still unapproved.

## Phase B B1 proposed sequences — 2026-10-15 (Claude, proposals only)

51. **Draft, not exit.** The seven proposed sequences and crash-window table follow the reviewed
    preferred D3/D7 design only; an alternative choice re-applies decision record §3.1 and
    updates the diagrams before B1 exit. Open plan ambiguities are recorded as assumptions A1–A5
    in the diagram file, not as plan edits.

## B1 sequence review completed — 2026-10-15 (Codex, no owner decisions)

52. **Close diagram corrections within the accepted plan.** Authorized receipt fast paths,
    terminal create/replay branches, cancel CAS-loser replay, dispatch fence, whole-bundle lease
    acknowledgement, serialized pending-intent recovery and complete incident-bundle dedup are
    explicit in draft rev2. Two peers re-reviewed the same cases PASS; no plan rev4/card added.
53. **Refresh facts, retain decision gates.** Six BE1 placeholders make the harness PASS now;
    the failed Claude run remains historical. BE1 occupies ADR-0016/0017, so decision record rev3
    proposes next-free0018 or feature-local adoption. Actual decisions are still absent. Stop
    adding preparation tasks; record real inputs, reconcile the draft and obtain separate code
    approval. Source/tests/Phase A approval remain unchanged by this documentation review.

## Owner selection — 2026-10-15

54. **Record actual acceptance with bounded context.** User's exact reply "Ổn đó" accepts the
    immediately preceding recommendation: preferred D1–D7, strong fence with fixture-first proof,
    current fixture test profile and running the missing Phase A test before acceptance. O-01
    and ADR-0018 record architecture selection; detailed owner-contract answers, role concurrence,
    actual Phase A disposition, runtime evidence and code approval are not supplied by that reply.
55. **Inventory existing environment before selecting it.** User's exact answer "Chưa rõ; cần
    kiểm kê môi trường hiện có" requests read-only inventory (O-02). No E1/E2 target, package
    install, service start or cloud spending is inferred. Local inventory cannot establish a
    remote Linux target's readiness. Preserve the existing one-batch implementation limit.

56. **Separate backend test Studio (O-03).** Exact user reply: "tên gì ? g coi như tạo mới lun đi". Select a new CPU Studio with working name sketch2life-backend-test, preserving FEAT-018. Creation requested, not completed; no service readiness or Phase B code approval inferred.

57. **Record real runtime evidence, retain acceptance scope.** O-08 user output establishes the
selected environment baseline, observed dependency versions within bounds, authenticated services
and the missing live-route1 passed,0 skipped. This does not prove Phase B durability or real owner
integration and is not Phase A acceptance/code approval. Original skipped run is historical.
58. **One reviewable component decision packet.** Decision record rev8 §13 proposes concrete
candidate checkpoint/Q1–Q8 fixture-bound answers, test key/environment mechanism and B1–B6 code
scope with B2-only first turn/review. No role sign-off or approval is fabricated. Do not request
new inventory/plan revisions; record a genuine owner reply before Claude starts implementation.

## Actual Phase B approval and bounded handoff —2026-10-15

59. **Record actual O-09 without enlarging authority.** The project owner accepts Phase A
candidate/fixture and decision record revision8 §13 as PROJECT_OWNER_DIRECTIVE, explicitly not
P1/P2/P4 sign-off; approves planrev3 B1–B6 on sketch2life-backend-test. Exact reply is in the
explicitly requested approvals/PHASE_B_TASK_APPROVAL.md; Phase A approval and approved plans unchanged.
60. **Close B1, hand off B2 only.** Q1–Q8 and seven diagrams/twelve crash windows agree with
accepted D1–D7; B1 CLOSED_COMPONENT_SCOPE, Q00 ACCEPTED_CANDIDATE_FIXTURE, ACTIVE Q01/B2
READY_FOR_CLAUDE. Claude implements schema/migrations and validation, stops B2_READY_FOR_REVIEW
before B3. Reuse approval for unchanged B1–B6 scope. Runtime/adoption/real integration remain
future; cards14/WIP1/fullDONE0, no new planning batch/card/approval loop or commit/push/deploy.

## Phase B B2 — 2026-10-15 (Claude, implementation)

61. **Independent `ai_jobs` Alembic branch.** No FK into BE1, so the branch has no BE1 dependency
    (Q7 dependency graph); explicit `ai_jobs@head` / `be1_core@head` / `heads` commands replace plain
    `head`, which now fails safely. BE1 procedures still saying `upgrade head` are flagged to P2/P4.
62. **Evidence tied to the exact snapshot.** PostgreSQL B2 checks count only when run on the Studio
    against `993a26c` + the hash-pinned B2 patch; until then they are NOT_RUN and B2 is not
    READY_FOR_REVIEW.

## Independent B2 review —2026-10-15 (Codex)

63. **Keep the accepted contract domain in SQL.** B2-R01 requires the five job_type/purpose_code
columns to preserve OpaqueId120; current metadata/migration80 is a schema regression. Keep80
only for real ErrorCode values. Correct schema/tests without narrowing Phase A contracts.
64. **Trust the exact tested snapshot and real exit status.** B2-R02 requires nonzero on failed
setup/test suites and verified retry of the exact already-applied package, never reset/clean.
Rebuild hashes after fixes; upload patch+manifest+runner. PostgreSQL evidence stays NOT_RUN until
actual named-Studio execution. Corrections stay in Q01/B2 with existing approval/cards14/WIP1;
Codex reviews, Claude fixes; no B3 or commit/push/deploy.

65. **Transfer context without restarting the task.** User asks for an extensive prompt for the
current Claude session to write a durable handover and a bootstrap prompt for a fresh session.
The transfer captures actual approval, current B2-R01/R02 review and local/Studio provenance;
it adds no card, implementation checkpoint, approval or permission. Old turn docs-only; new
session verifies actual sources then resumes the existing approved B2 work order. Prompt: evidence/local/claude/prompts/CLAUDE_WRITE_SESSION_HANDOVER_PROMPT.md.

66. **Apply the four handover wording corrections without changing scope.** User explicitly asks
Codex to revise the outgoing handover/bootstrap after review. Read paths/context are explicit;
future acceptance covers all current B2 tests including new regressions, zero PostgreSQL skips,
no Phase A failures and successful required runner steps. Remote migration execution remains
unverified, and offline/mock PASS applies only to its test scope. Q01/B2 findings and existing
approvals are unchanged; no backend/test/runner implementation is edited by this correction.

## User-authorized Codex B2 correction —2026-10-15

67. **Change executor within the approved B2 scope.** After Claude usage limit the user explicitly
asks Codex to continue and update the handover. Exact reply is recorded in B2_CODEX_EXECUTOR_HANDOFF_20261015.md.
Preserve original approvals/plan bytes; only executor routing is superseded, never P1/P2/P4 sign-off.
68. **Complete the two bounded local corrections.** Five opaque-ID columns use128 in metadata/
initialmigration, accepted contracts unchanged/ErrorCode80 preserved;81/120 localcontract+fixture+DDL
regressions pass and realPGroundtrips are added. Runner preserves statuses/logs, validates source
beforebothsuites, supports exactverifiedretry and rejectsunknownchanges;26mockcasesPASS. Independent
code reviewsPASS only within local/offline scope. No other backendfiles beyondthree changed.
69. **Hand over the next real step.** New f388ce36…419bff package/manifest/runnerZIP verified against
pristine993a26c and current eightfilehashes. Update handover/bootstrap to await actual Studio
PostgreSQL run rather than repeat old fixes.10PGcases NOT_RUN; allcurrenttests/noPGskip/PhaseAnoFailures/
runner0 and finalB2review required beforeB3. Same14cards/WIP1/fullDONE0, no commit/push/deploy.

## Studio B2 closure —2026-10-15

70. **Accept attributable real test evidence.** Exactf388patch/sourcehashes verified onStudio
by user; reported18B2passed/0skip +224PhaseApassed/0skip and explicit testexit0. Preserve
USER_REPORTED_REMOTE provenance. Two finalwrapperfields were not pasted; recordNOT_REPORTED,
neverinfer0, and do not add a rerun gate without a materialfailure. Codexreviewed localhash/
coverage and existingcode/mockproofs, not directly executed these remote tests.
71. **Close B2 only, route B3 under existing approval.** Independent closureauditsPASS atschema/
migration scope. R01/R02closed, B2_CLOSED_REVIEW_PASS; nextQ01/B3READY, codeNOT_STARTED.
B2review stop satisfied, PhaseBrev3B1–B6approval unchanged. Preserve14cards/WIP1/fullDONE0;
B01fullrestart/B11fullconformance/B12actualintegration remainlaterbatches. No backendchange or
provider/commit/push/deploy in this closureturn; currenthandover/bootstrap nowrouteB3.

## User-selected two-step Claude continuation —2026-10-15

72. **Separate takeover from execution in the same new Claude session.** User asks Codex to
update the handover while waiting for Claude availability and provide two pasteable steps.
Step 1 reads/verifies sources and reports understanding, then STOPS with no edits/tests/status
writes or remote actions. Only after user sends step 2 does Claude implement the already-approved
B3 scope and stop for review before B4. Existing B1–B6 approval, B2 closure, 14 cards/WIP1 and
B3_READY_FOR_IMPLEMENTATION/code NOT_STARTED remain unchanged. This interaction is not a new
approval or roadmap gate. Historical one-turn bootstrap execution wording is superseded.

## Phase B batch B3 —2026-10-15

73. **Decide outside, hold inside.** Every fenced use case reads, takes owner decisions outside
any write transaction, then re-reads with `FOR UPDATE`, holds the decisions' fences before any
mutation and commits; stale or missing fence ⇒ rollback and one re-decision, else a typed
retryable outcome. A missing fence is never current. Job rows are locked in write rounds, so
CAS conflicts indicate a bug rather than a normal race.
74. **One candidate, whole rollback.** Create writes job, attempt, semantic row, receipt, dispatch
row and audit intent with plain INSERTs; a unique violation rolls everything back and a fresh
round re-reads the winner (two rounds, then `409 IDEMPOTENCY_CONFLICT`). Semantic identity is
only the canonical NFC sha256 (Δ4) in both fake and SQL stores.
75. **Stay inside B3.** Dispatch fence (B4 Δ6/A2), completion/incident/quarantine intents (B5
Δ9/Δ15), notices (Δ10), capability/worker (Δ8/Δ14) are not implemented; SQL methods owned by
those batches raise `NotImplementedError`. Completion side effects move after commit so rolled-
back rounds have none. Owner fence is the test-only ASSUMED_CONTRACT fixture; real P2 = B-12.
76. **PostgreSQL proof by exact package.** B3 acceptance is PostgreSQL-only; without Studio access
the executor prepares patch a2e479d5… on top of B2 f388, a 19-file manifest and a runner that
fails on any skip and always prints outer exit/`RUNNER_RESULT`. Until the user's run, B3 stays
B3_CODE_COMPLETE with PostgreSQL NOT_RUN, not B3_READY_FOR_REVIEW.

## B3 independent review after reported Studio run —2026-10-15

77. **Keep reported test execution distinct from review closure.** User reports69B2+B3passed/
0skip, Phase A exit/log0/skipgatePASS and all outer/operator exits0. Default fixture20PASS/
215checks still has one optional HTTP NOT_RUN. Preserve USER_REPORTED_REMOTE and mark absent
source header/receipt timestamp/Phase A count NOT_REPORTED, not invented values. Local19source
hashes match the instructed package; no direct Codex cloud execution or full integration claim.
78. **Correct mixed-version aggregate reads within B3.** Independent review B3-R01/P2 reproduces
queued revision1 with started attempt via separate unlocked READ COMMITTED SELECTs. Existing
wire validator rejects the impossible aggregate; old69tests do not cover the schedule. Keep
B3_NEEDS_REVISION and Claude executor; fix repository consistency plus deterministic PG
regression, not validation/plan/BE1. New package must safely advance the known old B3 Studio
snapshot; no reset or blind overwrite. New-source runtime proof and review before B4, same
approval/cards14/WIP1; no backend implementation changed by this review.

## User-requested local operator prompts —2026-10-15

79. **Keep execution prompts out of publication candidates.** User requests Markdown prompts
be moved to local storage to avoid accidental GitHub publication. Move15prompt files and the
session handover into ignored evidence/local/claude/, retaining original bytes and path/hash
mapping. Seven tracked sources become deletions for a later reviewed cleanup commit; do not
stage or rewrite history. Preserve original approval-linked plan/CLAUDE_BE2_HANDOFF.md and actual
executor authorization evidence; these are governance provenance. Update active references,
candidate lists and scoped ignore guards. Existing B3-R01 finding/approval/cards/WIP stay intact.

## B3-R01 correction —2026-10-15

80. **One snapshot per unlocked aggregate read.** The unlocked `get_job` uses a single
job⟕attempt statement, so READ COMMITTED returns one committed version. The locked path stays
lock-then-read because a joined `FOR UPDATE` can re-check a newer job row against older joined
rows. Invariant for later batches: aggregate writers write/lock the job row before attempts.
81. **Upgrade only a known snapshot.** The B3-R01 package accepts exactly the reported Studio
snapshot (manifest ea5cf57e) or the corrected one (retry), applies a 2-file delta, refuses
anything else without reset, and records the new regression's result on the old source as
before-evidence. Previous 69-pass result is retained, not reused as proof of the fix.

## B3 runtime closure —2026-10-15

82. **Accept corrected-source proof, correct the optional before label.** Full user log binds
20sourcehashes/0814manifest/f38delta to71B2+B3PASS/0skip,224PhaseAPASS/0skip,all exits0.
Two new PG start/retry races pass; independent SQL/test reviewPASS, B3-R01 CLOSED_B3_SCOPE and
B3_CLOSED_REVIEW_PASS. Keep USER_REPORTED_REMOTE. Before-helper exit2 was collectionIndexError
with0tests, NOT_PROVEN_SETUP_ERROR, never valid repro. Current realPG+code review+original
offline defect proof suffice; no new fullrerun gate. Default fixture optionalHTTP remainsNOT_RUN.
83. **Route B4 under existing approval, preserve local prompts.** NextQ01/B4READY/codeNOT_STARTED,
Claude B4only per existingplanrev3 and ignored local implementation prompt; review beforeB5.
Studio now has corrected B3manifest0814, package transition must use it.14cards/WIP1/fullDONE0;
no backend/package/approval/plan change or B4 implementation by this closure, no install/service/
provider/commit/push/deploy. Fullcrash/conformance/actualP2P4integration remain laterbatches.

## Phase B batch B4 —2026-10-15

84. **SQL-fenced dispatch, broker outside SQL.** Claim, acceptance and acknowledgement are three
short transactions; the broker call and capability minting sit between them with no SQL lock
held. Only the current owner+generation can mark, release or dispose a row; the acknowledgement
writes the delivered mark and attempt bookkeeping together under the job row lock, so a stale or
repeated acknowledgement changes nothing. Bookkeeping does not bump `job_revision`.
85. **Same-attempt recovery before policy retry.** The reconciler republishes an unstarted
active attempt (new dispatch row, same `attempt_id`) until 3 publishes, then applies
`record_dispatch_loss`; start and recovery serialise on the job row, a pending dispatch row
excludes the attempt from the sweep, so recovery cannot fan out.
86. **Targeted sweeps replace all-job scans.** Overdue-running and due-retry sweeps use indexed
queries and repeat pages until empty or no progress; no seen-marker or general scheduler.
87. **Runtime proof by exact package.** B4 acceptance needs real PostgreSQL + Redis/RQ; the package
upgrades only the closed B3 snapshot (or retries the exact B4 snapshot), runs with isolated
`be2_b4_<random>` queues and fails on any skip. Until the user's run B4 is B4_CODE_COMPLETE.
88. **Rebuild the wiped synthetic Studio environment on explicit request.** After a Studio stop
erased Docker state, the user authorized "cho phép dựng lại". The rebuild is idempotent, reuses the
original names/password file, pins PostgreSQL/Redis to recorded digests and packages to recorded
O-08 versions, and changes no source; B4 runtime proof stays NOT_RUN until the rerun.

## B4-RT01 operator package completion —2026-10-15

89. **Finish packaging the existing correction while Claude is unavailable.** User reports Claude
tokenlimituntil19:50 after the B4failure log. Preserve Claude's3changedbackend/testfiles; Codex
only packages/tests/updateshandover under unchangedB4approval. Oldruntime88PASS/7FAIL remains
USER_REPORTED_REMOTE; correctedruntimeNOT_RUN, B4-RT01OPEN. Exactold32manifest70b2a160 ->
3-filedelta44f3a80d ->new32manifest444cfead selfchecked; ZIPe1a76867 ready.8hostmockflows/local
regressions/lint/typePASS do not prove PGRedis. User runs newpackage on existingStudio, then
independentB4reviewbeforeB5; no newcard/approval, backendedit,install,recreate,commit/push/deploy.

## B4 corrected runtime and full review —2026-10-15

90. **Close RT01, retain the full-review defect.** User source-bound32-filemanifest444cfead run
97B2–B4PASS/0skip+224PhaseAPASS/0skip with all exits0 closes B4-RT01, USER_REPORTED_REMOTE.
Independent full review finds P2 B4-R01: due retry LIMIT returns an unchanged deferred prefix
forever, starving healthy later scopes. Actual51jobservice/fakeprobe confirms; no PG repro claim.
CurrentQ01/B4_NEEDS_REVISION, not fullB4closed; original88PASS/7FAIL stays historical.
91. **Bound the correction to B4 paging.** Claude fixes B4-R01 within approved Delta11, keeps
owner fences/CAS/retrypolicy, finite targeted traversal and fake/SQL parity. No persisted seen
marker, scheduler/new card/approval, B5 implementation or unchanged-package rerun. CurrentStudio
source444cfead is the next package base. Update source-bound runtime evidence and focused review
before B5. Codex review preserves backend/approvedplan/approval/packages; no commit/push/deploy.

## B4-R01 fix —2026-10-15

92. **Page sweeps with a per-invocation keyset cursor.** B4-R01 is fixed by continuing each sweep
strictly after the last row's `(sort time, unique id)` key, using the query's existing ORDER BY,
with `now` fixed per invocation and a stop on the first short page. Rejected: larger LIMIT, full
scan, persisted seen markers, schedulers/queues, auto-cancelling blocked jobs, retry-policy or
fence changes. Rows that move behind the cursor or become due after `now` belong to the next
invocation. Status FIXED_PENDING_RUNTIME_REVIEW: Codex package review, a source-bound Studio run
(104 B2–B4 + 224 Phase A, 0 skips) and a focused closure review gate B4 closure and B5.

## B4-R01 independent fix review —2026-10-15

93. **Accept the code/package review, keep runtime closure pending.** Codex primary and SQL,
service/tests and package reviewers found no actionable issue in the six-file keyset correction.
18B4unitPASS, independent tied-key/multiple-page/restoration/all-deferred service probePASS and
SQLcompile/mapping4PASS;32sourcehashes/6deltafiles/4ZIPmembers verified,104casescollected. Current
Q01/B4_FIXED_PENDING_RUNTIME_REVIEW. Localf1c6834f differs from last-reportedStudio444cfead;
user runs ZIPa7afd57a, then focusedclosurebeforeB5. No newapproval/card or B4closureclaim.
Correct inaccurate POSIX-only skip wording to missingPillow per raw log; update stale bootstrap/
handover so no repeatedfix. Reviews preserve backend/approvedplan/approval/packagebytes.

## B4 runtime closure and B5 routing —2026-10-15

94. **Close B4 on the exact reviewed source.** Fulluserlog32manifestf1c6834f/delta56af4fbd,
104B2–B4PASS/0skip+224PhaseAPASS/0skip/all exits0 and independent source/package/bindingaudit
close B4-R01 andB4component scope. ProvenanceUSER_REPORTED_REMOTE; no directCodexcloudclaim.
FixtureoptionalHTTPNOT_RUN1 and75knownAlembicdeprecations remain labelled; no newrerun gate.
95. **Route unchanged approved B5 to Claude.** ACTIVEQ01/B5READY/codeNOT_STARTED, original
PhaseBrev3B1–B6approval; B5only Delta8/9/10/14/15 plusfakeparity, reviewbeforeB6. Local/Studio
sourcef1c6834f is nextpackagebase; no repeatB4/environmentsetup, newcard/approval or fullDONE.
Workorder stays ignoredlocalClaude prompt; closure editsdocs/evidence only, preserves source/
packages/approvedplans/approvals/index; no install/provider/service/stage/commit/push/deploy.

## B5 implementation —2026-10-15

96. **Durable side effects: deliver after commit, then lease and redeliver.** Intents commit with
their decision. The service delivers each once right after commit (best effort, which keeps
Phase A's observable behaviour). `deliver_side_effects` leases (SKIP LOCKED, generation+1), applies
outside SQL and marks the row as the current holder. Sinks deduplicate by event id. Create and
cancel deliver their stored event, never a second id-less one. The dispatch ack is not reused.
97. **Deterministic identities.** Audit: kind/type/job/attempt/claim fingerprint/reason.
Quarantine: the same plus sorted owned refs. Neither uses receipt id, clock or token. B3
create/cancel ids are kept. Direct (non-outbox) audits use revision-based ids; their durability
is not extended (start, dispatch, retry and dispatch-loss audits stay direct).
98. **Typed outcomes.** An incident that cannot commit is `DEPENDENCY_UNAVAILABLE` 503, retryable.
An oversized notice is `NOTICE_ATOMIC_LIMIT` 409, not retryable, with nothing changed (bound 100,
fixture only). Unrelated unique conflicts are re-raised, never swallowed.
99. **Capability format.** wcap.v1 HMAC-SHA256 over j/a/iat/exp in ms. Fixture TTL 40 s. Several
keys can verify, for rotation overlap. The token is authenticated before its claims are parsed.
The service checks expiry again. There is no issued_at ≤ now check, because fixture clocks differ
across processes. Provisioning stays with INTG-02.
100. **Package scope disclosure.** The B5 delta carries the earlier owner-approved Q00 EOF fix of
test_ai_job_q00_followups.py, because Studio still has the base version. Status is
B5_CODE_COMPLETE — PENDING_CODEX_REVIEW; Studio runtime and closure review gate B6. Evidence:
evidence/notes/PHASE_B_B5_IMPLEMENTATION_EVIDENCE_20261015.md.

## B5 independent review —2026-10-15

101. **Hold B5 for two demonstrated corrections.** Existing49B5unitPASS/fixturebaseline and
valid43sourcepackage do not cover cross-sink outboxstarvation (R01) or acceptedmalformedtoken
escapingredaction (R02). BothP2OPEN; actualservice/fake/HMAC/logprobesconfirmed, SQLselection
matchesR01. NoPGrepro/privilegeescalationclaim; B5notclosed/B6notstarted.
102. **Keep the fixes within existing B5.** SamePhaseBrev3approval, Claude fixesR01/R02only,
preservingleases/dedup/binding/expiry/policy. Optionalduplicateproviderteststrengthening is
not athirdgate. CurrentZIP9475historical; Studio remainsf1c, so newcorrectedpackage starts
there. Reviewnewcode/package beforeuserStudio, thenclosurebeforeB6;14cards/WIP1/fullDONE0.
Docs/evidence/handoverupdated,535source/package/approval/planpaths andindex preserved.

## B5 fix01 —2026-10-15

103. **Fair side-effect delivery by per-invocation keyset traversal (B5-R01).** This reuses the
reviewed B4-R01 pattern: strict `(created_at, message_id)` continuation, fixed `now`, stop on a
short page. Failing rows are released and retried next invocation. Rejected: larger LIMIT, a
persisted backoff marker, new schema/queue/scheduler, dropping work.
104. **Strict capability encoding and defensive redaction (B5-R02).** Whole-token shape plus
canonical unpadded base64url before the MAC. The scrub pattern matches any `wcap.v1.`-prefixed
run, case-insensitive. The filter scrubs all extras and rendered objects. Authority, scope, TTL,
rotation and replay are unchanged. Package b5fix01 starts from f1c6834f and refuses the unrun old
B5 source. Evidence: evidence/notes/PHASE_B_B5_FIX01_EVIDENCE_20261015.md.


## B5 fix02 Codex takeover —2026-10-15

105. **Explicit executor override, existing approval.** User asked Codex to finish the interrupted
B5 correction and summarize it for Claude: “:)))) tạm thời bạn làm đi tí bàn giao tóm tắt lại cho claude vì nó làm tới đây thì hết token nè”. This changes the executor for this
bounded correction, not the Phase B approval, plan, ADR or P1/P2/P4 ownership. Source:
evidence/notes/PHASE_B_B5_FIX02_CODEX_REVIEW_20261015.md; original approvals preserved verbatim.
106. **Complete the same two corrections.** B5-R01: fair keyset traversal passes failed sinks and captures the initial pending side-effect count as a finite row budget. At most that many claims/attempts occur per invocation; each claimed row is passed once, failures are released, and continuing arrivals cannot extend the budget. This is not a fixed-membership snapshot or wall-clock deadline; under concurrency new arrivals may consume the remaining budget. SQL/fake parity, generation leases, sink event-id dedup and dispatch bookkeeping stay intact. B5-R02: strict canonical whole-token acceptance retained; log messages are interpolated before scrubbing and arguments cleared; nested mapping keys and values are scrubbed. These are bounded corrections to the existing two findings, not new cards or architecture.
107. **Review is not remote execution or closure.** Direct local: B2-B5 97 passed / 96 PostgreSQL/Redis skipped (NOT_RUN); 57 B5 unit cases. Phase A 223 passed / 1 Pillow skip. Fixture baseline stays
20 PASS / 215 checks / d17f58a3, optional HTTP NOT_RUN 1. Last reported Studio remains closed B4 manifest f1c6834f41dc798fe4475509b7d4b9c8c578ebfd15f34ff07f72f2d4bf24aeb4: 104 B2-B4 + 224 Phase A passed / 0 skipped, all exits 0, 2026-10-15T13:26:49Z, USER_REPORTED_REMOTE. No B5 runtime has been reported.
Current Q01/B5_FIXED_PENDING_RUNTIME_REVIEW; B5-R01/R02 FIXED_PENDING_RUNTIME_REVIEW; fix02 package is the only next run.
Expected Studio: 193 B2-B5 passed / 0 skipped and 224 Phase A passed / 0 skipped; these are expected counts, not reported results. User supplies actual runtime, then focused closure; B6 needs explicit continuation.
108. **Preserve evidence and hand back the exact checkpoint.** Keep old B5/fix01 packages and
their failures/checks as history; do not apply them. New package 43-file manifest cf196e845d30179c2aa2b89e09970ccaf83777aa6d90fac7b29f68d091ad60d0, delta 3049e1bbb6988161422e1187b68ac4e197cb95047b0a6fd22e13cb983359d0ba, runner 65ec10bade2105254f46b5c2f400d2ebcf5d5ca733bb23fb208d5fdc65bbe767, ZIP 8887a635fcd2b996982a762f539af9016c39d45903876ea4a2e7a7406e98e76e.
Handover §X and evidence/local/claude/handover/CLAUDE_B5_CODEX_HANDOVER_20261015.md tell Claude to rehydrate read-only without redoing B5.
B1-B4 remain closed; B6 NOT_STARTED. Same Phase B revision 3 approval, 14 cards / WIP 1 / full-card DONE 0 / parent BE2-01 IN_PROGRESS. OwnerFence remains ASSUMED_CONTRACT; real B-12 integration deferred. No other card/provider/live router/BE1-owned writes/production/FEAT-018/Wan, install/service recreation/staging/commit/push/deploy.


## B5 Studio environment retry —2026-10-16

109. **Separate host-source application from runtime execution.** Latest USER_REPORTED_REMOTE attempt 2026-10-15T17:06:29Z (2026-10-16 00:06:29 +07): fix02 package hashes passed; source_state=b4r01_snapshot, then the patch applied and all 43 source hashes verified as fix02 cf196e84. Docker then failed because network sketch2life-be2-net was absent: outer exit 125, RUNNER_RESULT=FAIL, studio_command_exit=125. No test container started and no tests ran. Latest reported Studio host source is therefore fix02, not B4. Last successful runtime remains the earlier B4 f1c6834f run: 104 B2-B4 + 224 Phase A passed / 0 skipped, all exits 0, USER_REPORTED_REMOTE. No B5 runtime PASS is claimed.
Next: run the existing /teamspace/studios/this_studio/rebuild_be2_env.sh and wait for ENV_REBUILD_RESULT=PASS. Then run the SAME existing fix02 runner; expect source_state=b5fix02_snapshot_verify_only. Do not reapply the patch, build another ZIP or change code/environment scripts for this infrastructure-only failure. The existing runner already passed its Docker-125/verify-only-retry host simulation;
that mock proof is not remote runtime proof. Keep the failed remote attempt as environment
evidence and the earlier successful B4 run as the last PASS. Q01/B5_FIXED_PENDING_RUNTIME_REVIEW and B5-R01/R02 FIXED_PENDING_RUNTIME_REVIEW remain unchanged. B6 NOT_STARTED; 14 cards / WIP 1 / full-card DONE 0. Approved plans, approvals, ADR, source and packages stay frozen; no new finding/card.
Canonical recovery evidence: evidence/notes/PHASE_B_B5_STUDIO_ENV_RETRY_20261016.md; ignored attempt/operator receipts under
evidence/local/studio-env-retry-20261016/. No new script, ZIP, backend fix or approval is needed.


## B5 test-fixture runtime correction —2026-10-16

110. **Honor the failed whole-suite result while retaining actual passing evidence.** Latest actual Studio run 2026-10-15T17:12:17Z (2026-10-16 00:12:17 +07), USER_REPORTED_REMOTE, exact 43-file fix02 manifest cf196e84: 192 B2-B5 passed / 1 failed / 0 skipped; Phase A 224 passed / 0 skipped. Fixture 20 PASS / 215 checks / d17f58a3 unchanged, optional HTTP NOT_RUN 1. All 32 B5 PostgreSQL/Redis cases passed, but the whole parent suite failed (test/log exits 1/0, outer/operator 1). Studio host source remains fix02 cf196e84; B5 is not closed.
This supersedes the environment-only retry checkpoint: services recovered and tests actually ran.
Do not label fix02 193 PASS or discard the 192 actual passes and 224 Phase A passes.
111. **Use a cross-process capability fixture without weakening auth.** B5-RT01 is a test-fixture correction: the child dispatcher previously issued a capability into a process-local fake registry unknown to the parent. Only test_dispatch_recovery.py now shares an ephemeral HMAC key through spawn's pipe: child issuer, parent issuer/verifier. The original child bearer must start the attempt and the republished bearer must dedup. Crash exit 17, lease takeover, same attempt and dispatch-count assertions are preserved. No production code/auth rule or schema changes.
Independent actual spawn proof confirms both child and parent tokens work with the shared key,
while tampering, foreign attempt and expiry are denied. Key material stays ephemeral and never
enters SQL, Redis/RQ payloads, environment files or logs. The broker carries the capability only.
112. **One-file package, same approval and test count.** Fix03 starts only at exact 43-file
cf196e84 and produces manifest 3930046b5f04a67b6ff2a52dc70a4f12d5d7a89c2675e149ab654f00da2ab670, ZIP ff4b2484691babf0a30fde656f4d75793b0174855f8cf7671210146b2b4bb4f1.
Direct local: 97 B2-B5 passed / 96 PostgreSQL/Redis skipped (NOT_RUN for corrected source); Phase A 223 passed / 1 Pillow skip. Actual spawn/service-fake proof passes the original-child token and rejects tampered, wrong-attempt and expired tokens. No local PG/Redis execution. Review evidence/notes/PHASE_B_B5_FIX03_RUNTIME_CORRECTION_20261016.md. User runs reviewed fix03, then focused closure before explicit B6 continuation.
Same actual Phase B revision 3 B1-B6 approval; approvals, approved plans and ADR unchanged. 14 cards / WIP 1 / full-card DONE 0; parent BE2-01 IN_PROGRESS. No new business card, production auth change, provider/live router/BE1-owned writes/FEAT-018/Wan/install/service recreation/staging/commit/push/deploy. B6 NOT_STARTED.


## B5 source-bound runtime closure —2026-10-16

113. **Close the B5 component on the reviewed exact fix03 source.** USER_REPORTED_REMOTE fix03 run 2026-10-15T17:37:09Z (2026-10-16 00:37:09 Asia/Saigon): 193 B2-B5 passed / 0 failed / 0 skipped; 224 Phase A passed / 0 skipped; fixture 20 PASS / 215 checks / d17f58a3 unchanged (optional HTTP NOT_RUN 1). All suite/log/outer/Studio exits 0, RUNNER_RESULT=PASS. 43 source files verified as fix03 3930046b; local and reported Studio source match.
B5-R01 (finite fair side-effect delivery), B5-R02 (canonical capability and log redaction),
B5-RT01 (cross-process test key sharing) are CLOSED_B5_SCOPE. Independent source/package/
runtime-binding review PASS; no code changes or repeated unchanged suite in this closure.
Evidence: evidence/notes/PHASE_B_B5_CLOSURE_REVIEW_20261016.md, matching metric, raw full user log kept locally.
114. **Hand back B6 without treating BE2-01 as DONE.** B6 NOT_STARTED: conformance runner, crash-point matrix, Phase A scenarios on SQL, consolidated report and handoff under existing approved Phase B revision 3 B1-B6. Claude first rehydrates read-only from latest handover section AA, reports and stops; B6 implementation follows the agreed separate continuation message, without repeat approval.
The current package baseline is fix03 3930046b5f04a67b6ff2a52dc70a4f12d5d7a89c2675e149ab654f00da2ab670. Do not reapply previous fixes,
rebuild the environment or repeat successful B5 testing for another approval. Keep earlier
failed/skipped reports and immutable package build-time NOT_RUN metadata as history.
Parent BE2-01 IN_PROGRESS; exactly 14 business cards / WIP 1 / full-card DONE 0. B1-B5 closed at their recorded component scopes, not whole-product completion. OwnerFence ASSUMED_CONTRACT; real P1/P2/P4 integration/B-12, providers, live router and production adoption remain deferred. No other card, FEAT-018/Wan, install, service recreation, staging, commit, push or deploy. Original approvals/plans/ADR unchanged.

115. **Provide a two-step Claude reset handover at the user request.** evidence/local/claude/handover/CLAUDE_RESET_HANDOVER_B5_TO_B6_20261016.md
summarizes R01/R02/RT01 corrections, actual fix03 193+224 PASS and exact source3930046b.
The first prompt is read-only/report/stop; the second starts only when the user sends it separately.
Existing approval applies to unchanged B6; no approval rewrite, new card, backend change or
B6 implementation occurs while preparing this artifact. Keep operator prompts Git-ignored.

116. **Use reviewed task branches through dev.** owner-branch-workflow-20261016. Actual user reply:
“làm xong merge vào dev xong tạo nhánh mới đk ? ok chốt v đi chờ claude làm tính tiếp”.
Owner confirmed: finish one BE2 card, review and integrate it into dev, then create the next task branch from updated dev. One branch per card; B1-B6 remain on the existing BE2-01 branch. Create task branches when needed, not all fourteen upfront. Keep per-card plans/approvals/evidence and the existing dependency order. Current branch feature/be2-01-ai-job-foundation stays unchanged while Claude handles the B6 handoff. This workflow decision performs no branch/commit/push/merge operation and does not authorize other-card implementation.

## B6 implementation —2026-10-16

117. **Durable conformance runner without fallback.** It classifies A-01..A-20 as required
durable (on the SQL adapter), contract_only, deferred (A-18, BE2-14) or optional (HTTP surface).
The crash windows and B-01..B-11 are resolved only from this run's own JUnit and reports. A skip
or missing evidence is NOT_RUN (exit 2) and any FAIL is exit 1. B-12 is HANDOFF and never PASS.
Isolation is one cloned database and one RQ queue per harness, all disposable and removed after
the run.
118. **Close the B-01 gap with real process kills.** `test_restart_recovery.py` covers W01
(before commit), W02/W08 (after commits; full-row checksum survives; restart publishes and
delivers) and W06 (after start; policy retry). The W07 provider/completion window stays bounded:
no claim journal.
119. **Additive B6 package.** The delta from fix03 `3930046b` only adds files; the closed B1–B5
source is untouched. Four pre-existing ruff I001 findings in unchanged fix03 files are recorded,
not edited. Runtime, review and closure gate B6; BE2-01 is not DONE. Evidence: evidence/notes/PHASE_B_B6_CONFORMANCE_EVIDENCE_20261016.md.

## B6-fix01 —2026-10-16

120. **B6-RT01 is a test defect; fix only the test and keep run 1 on record.** In the crash child,
`test_restart_recovery.py` piped the Attempt object, so the restart lookup failed before
asserting the receipt, outbox publication and side-effect delivery. That one test failure made
W02, W08, B-01 and B-06 FAIL; no durable scenario check failed. The fix is one line, with no
product, runner or mapping change. Package b6fix01 starts only from the exact Studio B6 snapshot
`3940e529`; any other source is refused untouched. Run 1 stays recorded as FAIL and is not
overwritten. B6 and BE2-01 stay open until review, a passing Studio run and closure. Evidence:
evidence/notes/PHASE_B_B6_CONFORMANCE_EVIDENCE_20261016.md §9.

## B6-fix01 pre-run review —2026-10-16

121. **User-directed author self-review replaces the Codex pre-run review for B6-fix01 only.**
The user's words: "codex hết token r phần này bạn làm lun đi xong tôi đi ngủ". Claude reviewed its own one-line fix and package. The review is
recorded as AUTHOR_SELF_REVIEW, not as independent review. It covers:
- a package audit along a path different from the builder;
- a static trace of lines 156–173 against the service and SQL code;
- a no-service probe.

It authorizes only the Studio run of b6fix01. It does not close B6. The B6/Phase B closure review
must be independent of the author, and it must reconcile Codex's B6 review record: that record's
summary lists no findings, while its own restart probe reproduced B6-RT01. Evidence:
evidence/notes/PHASE_B_B6_CONFORMANCE_EVIDENCE_20261016.md §10.


## Codex CR01 pre-commit snapshot review —2026-10-16

Review of runner 87f0961f / B6 unit f07a1f4c: NEEDS_REVISION for the CR01 hardening snapshot. Missing parametrized testcase [120] while retaining [81] still yields G-01 PASS (211 of 212 collected B2-B6 cases). Compare full collected testcase identities, including parameter IDs; add focused regressions. Direct local B6 units16 PASS, ruff/mypy/harness/architecture/security/diff PASS; PostgreSQL/Redis NOT_RUN locally. The older 90724453 runtime and publication dry run do not cover these two changed files. This is a source-bound reviewer observation, not an owner decision or a new task/approval. See evidence/notes/PHASE_B_B6_CR01_CODEX_PRECOMMIT_REVIEW_20261016.md. Later source requires rechecking. Same approved Phase B scope; BE2-01 IN_PROGRESS, B-12 HANDOFF. No source/package/Git mutation by this review.

## B6-CR01 —2026-10-16

122. **Harden the durable runner for B6-CR01; keep the B4-RT01 evidence pair in the repository.**
Person 2's words: "Chọn làm cứng B6-CR01, giới hạn trong runner và test liên quan … Giữ cặp note/metrics B4-RT01 trong repo vì các evidence khác đang tham chiếu tới chúng.".
- **Scope.** The scope is run_durable_conformance.py and test_ai_job_b6_conformance.py only: the
  gates G-01..G-04 and inventory-aware W/B resolution, plus regressions for the review's cases.
  No product code changes.
- **Finding state.** CR01 stays FIXED_PENDING_RUNTIME_REVIEW until a Studio run of package b6cr01
  and a review of the fix.
- **Publication.** The plan publishes all 123 status paths (121 + the B4-RT01 pair) with the same
  content split as COMMIT_PLAN_V2.
- **Not decided here.** The owner's B6 closure entry is still pending. Evidence: evidence/notes/PHASE_B_B6_CONFORMANCE_EVIDENCE_20261016.md
  §12.


## Codex focused CR01 re-review —2026-10-16

PASS_LOCAL_PENDING_FINAL_PACKAGE_AND_RUNTIME on runner d42d697c and B6 unit b1d3bced. The earlier parameter-variant P2 is resolved: heldout B2-B6 and Phase A missing variants produce NOT_RUN; unmapped failure plus a missing variant produces FAIL/exit1; collection error fails closed. Direct local21 B6 units PASS, ruff/mypy PASS. Source hashes stayed stable through the probes. See evidence/notes/PHASE_B_B6_CR01_CODEX_PRECOMMIT_REVIEW_20261016.md (latest addendum) and ignored evidence/local/b6-cr01-codex-rereview-20261016/. Earlier ZIP d0b9f27b/a75841e0 package audit PASS applies to its immutable bytes; author edits advanced source beyond it. Final source-bound package/Studio result and refreshed publication dry run remain required. Runtime NOT_RUN locally; same approved B6 scope, BE2-01 IN_PROGRESS, B-12 HANDOFF. No code/approval/Git operation by this review.

## B6-CR01 r2 —2026-10-16

123. **Correct the CR01 completeness gate with pytest-collected identities, as revision r2.**
- **Scope.** The Codex pre-commit P2 is a correction within the current B6 scope under the
  existing Phase B approval: no new task and no approval change. Only the runner and its unit
  tests change.
- **Rule.** The expected inventory comes only from `pytest --collect-only` of the running tree,
  never from the JUnit under evaluation. Identities include the path, class parts and parameter
  id. Collection is all-or-nothing.
- **Packaging.** The new package is named b6cr01r2. The never-run b6cr01 package stays unchanged
  and is refused by the r2 runner as a source state.
- **Before the Studio run:** a Codex review of the fix and the package.
- **After the Studio run:** a review before CR01 closes.
- **Correction to an earlier record.** The first b6cr01 build (575aa8f4) was overwritten in place
  by its rebuild before anyone ran it.

Evidence: evidence/notes/PHASE_B_B6_CONFORMANCE_EVIDENCE_20261016.md §12.6.


## Codex R2 code/package pre-run review —2026-10-16

**Q01/B6_CR01_R2_CODE_PACKAGE_REVIEW_PASS_PENDING_RUNTIME** on 46-file manifest cb527d7f and ZIP 3a9d6ef2. The reviewed source is runner d42d697c / B6 unit b1d3bced. Independent local21 B6 tests PASS; heldout missing B2-B6/Phase A parameter variants are NOT_RUN; unmapped failure with a missing variant yields FAIL/exit1; collection errors fail closed. R2 package audit PASS: 46/46 current hashes, ZIP4 members, two-file delta from90724453, scratch apply/reverse, shell syntax, source-state pins and exit/skip guards. No actionable finding remains in this focused pre-run scope. Studio runtime is NOT_RUN; CR01 remains FIXED_PENDING_RUNTIME_REVIEW, not closed. See evidence/notes/PHASE_B_B6_CR01_CODEX_PRECOMMIT_REVIEW_20261016.md, latest R2 addendum. Next: run only b6cr01r2 on the approved synthetic Studio, review the source-bound results, then refresh publication documents and dry run. BE2-01 IN_PROGRESS, B-12 HANDOFF; approvals and source/packages unchanged by review. No staging/commit/push/merge/deploy.

## Local checkpoint commits before the r2 Studio run —2026-10-16

124. **Commit the reviewed BE2-01 state locally before runtime r2; runtime and closure stay pending.**
Person 2's words: "tạo các COMMIT LOCAL để lưu checkpoint BE2-01 hiện tại, không chờ Lightning phục hồi."
The Lightning Studio is not usable now.
- **Authorized.** Update the plan and state documents, run a fresh dry run and the required
  validators, then create the 21-commit chain of COMMIT_PLAN_V2 on `feature/be2-01-ai-job-foundation`,
  imported by a guarded `update-ref` from base `993a26cae78c0a4fe983033f03881838c886b176`. This
  replaces the plan's "Studio r2 before commit" order and the earlier read-only bootstrap stop.
- **Not authorized / unchanged.** No push, merge, deploy, Studio run, or source, test and package
  change. Runtime r2 is NOT_RUN; B6-CR01 stays FIXED_PENDING_RUNTIME_REVIEW; the owner's B6 closure
  entry is still pending; BE2-01 is IN_PROGRESS; B-12 is HANDOFF; OwnerFence/audit/artifact stay
  ASSUMED_CONTRACT. No P1/P2/P4 sign-off and no acceptance are created. The approval records are
  not changed.
- **Truthful scope.** The commits save reviewed work; they are not acceptance. Three source commits
  reproduce Studio snapshots that had failing tests, corrected by the commits that follow (B4
  88 passed / 7 failed, B5 192 / 1, B6 201 / 1); not every commit is test-green. Commit 18 records
  code/package review PASS (Codex) with Studio runtime NOT_RUN.
- **Studio.** It keeps base `993a26c` and source `90724453`. Do not pull, reset or check out there:
  the r2 package pins base `993a26c` and applies its delta from `90724453`, so the local commits do
  not invalidate it. Later runtime and closure results go into follow-up commits, with no amend or
  rebase of the checkpoint chain.

## Codex A17-fix01 received-evidence review and local port —2026-10-16

Technical checkpoint, not an owner closure decision: received archive3bcaa058 passes integrity
and raw-receipt review (cloud221 B2–B6 +224 Phase A,0 failure/error/skip;43/43 required durable
PASS). A17-fix01 fixes a scenario message-order premise; no production authorization bypass
was reproduced. The exact runner/test patch e9234446 is applied locally on HEAD8825e9ff;
manifest5b76868d matches46/46 source files;local25 B6 units and focusedruff/mypy PASS.
Scope stays the approved B6 runner correction, with original approvals unchanged. The cloud
test-role pg_signal_backend adjustment is evidence context, not a Studio/production directive.
Prepare a new immutable A17-fix01 Studio package; retain old packages and FAIL receipts.
Studio A17-fix01 NOT_RUN; CR01/B6 closure pending; BE2-01 IN_PROGRESS; B-12 HANDOFF; OwnerFence
ASSUMED_CONTRACT. No staging/commit/push/merge/deploy. Evidence:
evidence/notes/PHASE_B_B6_A17FIX01_CLOUD_RECEIPT_REVIEW_20261016.md.

## Publish the A17 checkpoint and hand off the second BE2 lane —2026-10-16

125. **Split focused commits and push the existing BE2 feature branch for teammate access.**
Direct user request (verbatim): "lên plan tách commit ra đẩy lên github cho tk kia lấy về tạo nhánh mới đi".

- Authorized: prepare a concrete commit split, run the required checks, create focused follow-up
  commits on `feature/be2-01-ai-job-foundation`, then push that named branch normally to origin.
  Publish code, sanitized evidence summaries and the repository-facing handoff. Raw ZIPs/logs,
  private environment data and personal AI prompts remain ignored/local. Do not amend/rebase the
  earlier21-commit checkpoint chain or force-push.
- Allocation already confirmed by the user: sender BE2-01–07; second executor BE2-08–14,
  seven cards each. BE2-07/DATA-26/CMD-38–39 remains sender-owned; the teammate consumes its
  versioned knowledge/script output for08–10. Implementation WIP stays1 until separately recorded
  coordination/approval enables another code checkpoint; planning may proceed in parallel.
- Base for the requested new branch: dev does not yet contain this foundation checkpoint at
  publication preflight. The teammate may create a candidate BE2-12 planning branch from the
  fetched foundation feature branch and record that base and unresolved Studio/integration gates.
  This is an early planning handoff; it does not merge unfinished BE2-01 into dev or automatically
  authorize BE2-12 code. Subsequent runtime cards still require their own feature plan/approval.
- Unchanged: Studio A17-fix01 NOT_RUN, B6-CR01 FIXED_PENDING_RUNTIME_REVIEW, BE2-01 IN_PROGRESS,
  B-12 HANDOFF, OwnerFence ASSUMED_CONTRACT. No owner closure/P1/P2/P4 sign-off, deployment or
  database privilege changes. Original Phase A/Phase B approval records remain byte-identical.
- Studio keeps its pinned993a26c base/source state; do not pull these checkpoint commits there.
  The separately prepared A17 Studio package has its own supported-state checks.

Public entry point: artifacts/BE2_08_14_TEAMMATE_HANDOFF.md. Exact publication commit plan and
receipts remain feature-local; pushed commit hashes are reported after successful publication.

## Owner-directed cross-lane shared UoW disposition — 2026-10-21

The owner directed that BE2-01 own the shared foundation UoW/authorized transaction
boundary for the separate video submission and finalization commits, with BE2-08
participating only in its own rows and never committing the foundation UoW. Resolve
job → run → source pin from authoritative persisted foundation job/request/attempt
data; keep WorkerDispatchEnvelope unchanged. This does not authorize adding
unapproved envelope fields or direct writes to foundation tables.

The new draft scope is
plan/CROSS_LANE_FOUNDATION_UOW_SCOPE_DRAFT_20261021.md, SHA256
B456DEEDF5F892F328E7AEEFF442BC82281400A994EB5A74D791C13856FAB9B0.
It is a new draft requiring independent review, exact final SHA and supplemental
implementation approval. The already-approved typed-route scope does not include
this UoW. No source/test/schema edit or card acceptance is authorized by this
decision entry. Preserve the separate-transaction boundary: no UoW remains open
during generation.

## Shared foundation UoW scope review follow-up — 2026-10-21

The first shared-UoW scope draft received an independent CHANGES_REQUIRED review. Its revision-2 response remains preserved at plan/CROSS_LANE_FOUNDATION_UOW_SCOPE_REV2_DRAFT_20261021.md (SHA256 39B0FD5958D2C298460F7605A7F73E8BDC7BC9D269B6399822FD2A2EAAC4DDC4); the later owner D1 selection A and its conditions are recorded in the current section above and FEAT-057's D1 receipt. Revision 3 is the current review target. X01 remains PARTIAL by default. The owner direction is not implementation approval and does not alter the typed-route approval or BE2-01 status.

## UoW scope rereview 2 — 2026-10-21

Claude returned CHANGES_REQUIRED on scope revision 3. The owner-pasted report is preserved in FEAT-057 evidence. Documentation successor: plan/CROSS_LANE_FOUNDATION_UOW_SCOPE_REV4_DRAFT_20261021.md (SHA256 9B96CA79FDA1DB8DFCBD2DFED6550ECA0645AD0C86CCEEAAF79793B0B7200381). It adds the complete writer inventory, existing-state mapping with BE2-10 exhaustion ownership still gated, corrected A/S/B/F rows and recovery, reject-only commit, lock/lease distinctions, receipt/run_json facts, full candidate fence inputs, get-by-job and participant API requirements, and adapter error handling. S/F still need independent review and separate supplemental approval. The draft changes no source, tests, approvals, card status or acceptance.

## Cross-lane UoW owner D2 — 2026-10-21

The owner selected the FEAT-057 D2 design: foundation SUCCEEDED with ResultDisposition.STALE maps to a distinct terminal stale representation on the BE2-08 video-run lifecycle axis, without artifact or ready-for-review state, through a versioned BE2-08 CR; do not add STALE to foundation JobState. VideoRun attempt_id is bound only at S; retry returns the video run to QUEUED and clears its prior attempt_id; attempt number remains foundation-owned. This is design direction, not implementation approval or card acceptance. See FEAT-057 evidence/notes/CROSS_LANE_UOW_OWNER_DECISION_D2_20261021.md and scope Rev5 draft.


## Owner adoption of BE2-VIDEO-LIFECYCLE/1 — 2026-10-22

The owner adopted the versioned A/S/B participant contract and identity-failure behavior under the hash-pinned FEAT-057 scope Rev2. BE2-01 owns transaction begin/commit/rollback, and BE2-08 participates through a typed transaction-bound contract without receiving a SQL connection through an application port. The unchanged envelope is consumed by the existing dispatch path. The three owner approval manifests were recorded and verified before source/test edits. This does not change FEAT-044 card acceptance/status. PostgreSQL 17 persistence evidence remains pending; see the FEAT-057 implementation checkpoint note.
