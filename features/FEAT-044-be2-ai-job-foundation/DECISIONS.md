# BE2 planning decisions — 2026-10-14

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
40. **Revision remains documentation.** Claude prepares rev2 through CLAUDE_PHASE_B_PLAN_REVISION_PROMPT.md; proposals remain PROPOSED and findings pending independent re-review. No approval/stack adoption/code from this review. Phase A code PASS retained; ACTIVE Q00 acceptance pending. Whole BE2-01 IN_PROGRESS.

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
