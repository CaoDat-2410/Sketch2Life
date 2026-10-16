# BE2-02 — Vision and correction provenance

- Status: APPROVED (C1_COMPONENT_OFFLINE; approval 2026-10-16 19:18 +07:00, verbatim in approvals/)
- Owner: BE2 / sender lane01–07; Claude implementation, Codex planning/review.
- Backlog/feature: BE2-02 / FEAT-048; not FEAT-002.
- Plan: plan/PLAN.md revision1 (approved bytes plan/PLAN_REV1_APPROVED.md), C1 only.
- Implementation status: IN_PROGRESS (card); C1_COMPONENT_OFFLINE ACCEPTED by owner 2026-10-16 21:26 +07:00 (approvals/C1_COMPONENT_ACCEPTANCE.md)
- Branch/base: feature/be2-02-vision-correction /6dcc57ee0b3d053f071c8c92e72aaaee2e98d899.
- Goal: source-bound observations and separate attributable corrections under current scope.
- Scope: strict candidate contracts, pure domain/application, narrow ports/fakes, offline V2
  reuse bridge, isolated CMD-34 fixture handler and focused evidence.
- Excluded: real provider/GPU/network/install, SQL/queue, production router/composition,
  other cards/FEAT-018 changes, commit/push/merge/deploy.

## Request and authority

User first requested BE2-02 requirements and a Claude-ready plan (planning only). On 2026-10-16
19:18 +07:00 the user sent the actual C1 approval (verbatim in approvals/TASK_APPROVAL.md; plan
SHA256 f4733c88…); Claude then implemented C1.1–C1.5 in this worktree only. Component candidate
approval; no production adoption, BE1/P1/P4 sign-off, commit, push or deploy.

## Source baseline and dependencies

Canonical Master SRS v3.1 + FEAT-040 card BE2-02; source IDs collaborative-srs-v3-20261010,
four-person-task-backlog-v1, owner-be2-roadmap-control-20261014. Read evidence/notes/SOURCE_AUDIT.md.
Component interpretations are PROPOSED in DECISIONS.md.

Foundation01 has published A17-fix01 and verified cloud evidence, but Studio NOT_RUN, CR01 open,
BE2-01 IN_PROGRESS and B-12 HANDOFF. This is a candidate foundation base, not closure/dev merge.
Existing implementation WIP limit1 remains. After genuine C1 approval record01 WAITING_STUDIO
and02 C1 ACTIVE before code. Teammate owns08–14 and may plan12 separately.

BE1 owns checkpoint/artifact/current authority/consent/age/turn/context. Existing ports do not
provide a full new meaning/context authority adapter; fixtures remain ASSUMED_CONTRACT.
Checkpoint JSON checksum differs from rendered PNG/JPEG hash. Legacy V2 has an injectable
offline seam but lacks typed topic/age/context; its adult narration hint cannot stand in for
Child intent. C1 bridge is explicitly image_only, not full FR022 real context-aware inference.

## C1 result —2026-10-16

Domain, contracts, ports, service, fakes, read-only BE2-01 lineage adapter, offline V2 bridge,
CMD-34 fixture router and tests landed (all uncommitted). Evidence and V01–V17 mapping:
evidence/notes/C1_IMPLEMENTATION_EVIDENCE.md; consumer handoff evidence/notes/H_AI_REVIEW_HANDOFF.md;
golden examples fixtures/h_ai_review/. Legacy finding F-01 (V2 adapter OSError branch) is
contained by the bridge, not fixed. Pillow-dependent checks are NOT_RUN.

## Next

Codex reviews C1. Remaining full-card gates (typed provider context, model adoption/quality,
real BE1/BE2-03 adapters, persistence/runtime, live composition) stay open; C1 is not DONE.

## Current review disposition —2026-10-16

Codex review is NEEDS_REVISION, 2 P1/4 P2 (C1-R01–R06), not C1 acceptance.
Read evidence/notes/C1_CODEX_REVIEW_20261016.md and its metrics before continuing.
Fix only these findings within approved C1; retain evidence, original approval and
approved plan bytes. Then stop for Codex re-review. N01 is non-blocking; qualified
owner-fence/immutable-job residuals are not promoted fixes. No publication, real
provider/runtime integration or full-card closure is authorized by this review.

## Review fixes —2026-10-16

User asked Claude to fix C1-R01–R06 per the review-fix prompt. Fixes and regressions landed
(uncommitted); candidate choices in DECISIONS "C1 review-fix candidate choices"; evidence
evidence/notes/C1_REVIEW_FIX_EVIDENCE_20261016.md. Disposition FIXED_PENDING_CODEX_REVIEW, not
CLOSED. Approval and approved plan bytes unchanged. N01, F-01 and Pillow NOT_RUN remain.

## Current Codex re-review —2026-10-16

Latest disposition NEEDS_REVISION: C1-R04 reference checks remain incomplete;
R01/R02/R03/R05/R06 CLOSED_C1_COMPONENT_SCOPE. Read evidence/notes/
C1_CODEX_REREVIEW_20261016.md before continuing. Fix only final-newline/fullmatch
and empty optional-ref handling with regression, then stop for re-review.
No new card/provider/runtime scope or approval. Previous reports above are history.

## R04 follow-up —2026-10-16

User asked Claude to fix only the two remaining R04 bypasses. `observation_bounds_violation` now
checks every non-None ref (empty strings included) with `fullmatch`. Regression: 12 fail before →
19 pass after; evidence evidence/notes/C1_R04_FOLLOWUP_EVIDENCE_20261016.md. Disposition
FIXED_PENDING_CODEX_REVIEW; approval/plan bytes unchanged; uncommitted; stop for re-review.

## Latest Codex R04 closure —2026-10-16

Read evidence/notes/C1_CODEX_R04_CLOSURE_20261016.md for the current disposition.
All six findings closed for C1; root focused suite 232/1 Pillow skip and original probes 6/6.
CODE_REVIEW_PASS_WITH_NOTES does not assert missing checks PASS or owner acceptance.
No new batch/card or Git action; BE2-02 IN_PROGRESS, BE2-01 WAITING_STUDIO.
Previous NEEDS_REVISION/FIXED_PENDING_CODEX_REVIEW entries are historical.

## Existing Pillow verification —2026-10-16

Seven V2 server tests now pass with existing Pillow12.1.0, no package installation
or shared-venv change. Only the production route walk still lacks python-multipart
among the named C1 follow-up checks. See evidence/notes/C1_REMAINING_CHECKS_20261016.md.
Existing approval excludes installs; any test-dependency installation needs a direct
user instruction. Code review/finding closures unchanged; no C1 owner acceptance.

## Latest complete C1 verification —2026-10-16

All six findings closed; focused233/233 + V2 server7/7 passed in one run, separate
foundation live-route1/1 also passed. No remaining Pillow/multipart skip among the
identified C1 checks. Original approval/plan/code unchanged; user continuation
authorized only the isolated declared multipart dependency and tests. Read
evidence/notes/C1_FINAL_VERIFICATION_20261016.md. C1 ready for owner acceptance;
full BE2-02 IN_PROGRESS, BE2-01 WAITING_STUDIO, no C2/publication action.

## C1 owner acceptance —2026-10-16 21:26 +07:00

User accepted C1_COMPONENT_OFFLINE on the Codex reviews and C1_FINAL_VERIFICATION_20261016.md
(verbatim: approvals/C1_COMPONENT_ACCEPTANCE.md). Component scope only; BE2-02 stays IN_PROGRESS;
N01, F-01 and out-of-C1 dependencies/integration stay open. TASK_APPROVAL.md and the approved plan
are unchanged. Next: review the commit plan in evidence/notes/C1_PUBLICATION_PLAN_20261016.md.
