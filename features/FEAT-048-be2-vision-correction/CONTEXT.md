# BE2-02 — Vision and correction provenance

- Status: APPROVED (C1_COMPONENT_OFFLINE 2026-10-16 19:18 +07:00; C2_TYPED_CONTEXT_OFFLINE 2026-10-17 11:20 +07:00; verbatim in approvals/)
- Owner: BE2 / sender lane01–07; Claude implementation, Codex planning/review.
- Backlog/feature: BE2-02 / FEAT-048; not FEAT-002.
- Plan: C1 plan/PLAN.md revision1 (approved bytes plan/PLAN_REV1_APPROVED.md); C2 plan/C2_TYPED_CONTEXT_PLAN.md revision2 (approved bytes plan/C2_TYPED_CONTEXT_PLAN_REV2_APPROVED.md).
- Implementation status: IN_PROGRESS (card); C1_COMPONENT_OFFLINE ACCEPTED by owner 2026-10-16 21:26 +07:00 (approvals/C1_COMPONENT_ACCEPTANCE.md); C2_TYPED_CONTEXT_OFFLINE ACCEPTED by owner 2026-10-17 11:59 +07:00 (approvals/C2_COMPONENT_ACCEPTANCE.md)
- Branch/base: feature/be2-02-vision-correction /6dcc57ee0b3d053f071c8c92e72aaaee2e98d899.
- Publication checkpoint: 8 C1 commits pushed at98876fe (receipt2026-10-16); C2 committed locally (52bf84f, 164575c + records/routing commits), not pushed. No merge/deploy.
- Publication: plan PUBLICATION_PLAN_REVIEW_PASS (four commits,37 paths, 6/17/11/3; evidence/notes/C2_PUBLICATION_PLAN_20261017.md) executed locally 2026-10-17 under the owner's instruction as four commits on feature/be2-02-vision-correction: 52bf84f (plan/approval/.gitattributes), 164575c (code/tests/typed golden), the following records commit and a shared-ledger routing commit; not pushed (push, merge and deploy need separate instructions).
- C2: C2_TYPED_CONTEXT_OFFLINE APPROVED 2026-10-17 11:20 +07:00 (verbatim approvals/C2_TASK_APPROVAL.md);
  plan revision2 SHA256 4b339514…, approved bytes plan/C2_TYPED_CONTEXT_PLAN_REV2_APPROVED.md; owner selected Q1–Q5 as recommended.
  Codex CODE_REVIEW_PASS_WITH_NOTES (evidence/notes/C2_CODEX_REVIEW_20261017.md); owner component acceptance
  2026-10-17 11:59 +07:00 (approvals/C2_COMPONENT_ACCEPTANCE.md). Committed locally per evidence/notes/C2_PUBLICATION_PLAN_20261017.md; not pushed.
- Goal: source-bound observations and separate attributable corrections under current scope.
- Scope: strict candidate contracts, pure domain/application, narrow ports/fakes, offline V2
  reuse bridge, isolated CMD-34 fixture handler and focused evidence.
- Excluded: real provider/GPU/network/install, SQL/queue, production router/composition,
  other cards/FEAT-018 changes, commit/push/merge/deploy.

## Request and authority

Latest request2026-10-17: “th chuẩn bị c2 đi lên plan cho tôi sau đó lấy prompt cho claude làm”.
Plan/prompt preparation is authorized while Lightning is unavailable; C2 implementation is not
yet approved. Planrev2 separates internal owner facts/provider payload, pins typed context,
preserves historical receipt replay and versions typed records separately from image_only.
Review/evidence: evidence/notes/C2_PLAN_REVIEW_20261017.md. Prompt/approval template stays ignored
under evidence/local/claude/prompts/. User submission of a genuine plan-specific approval is
required before code; finding a template on disk is not approval. BE2-01 Studio review still
has priority when usable. Older dated routing below records prior checkpoints.

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
are unchanged. The approved commit plan was executed locally (see Publication above); push needs a
separate owner instruction. BE2-01 stays WAITING_STUDIO.

## Resume order for 2026-10-17 — latest user instruction

User: “Xong cái này note lại đi mai lighing bth làm xong task 1 xong làm tiếp task 2 này”.
Work order: BE2-01 pending Studio A17-fix01 run -> Codex receipt review -> applicable
closure/owner acceptance first; then BE2-02 C2 plan review/Q1–Q5 and plan-specific
approval before code. This is scheduling intent, not C2 approval or confirmation
that Lightning has recovered. WIP1 preserved; no new card/code opened.

C1 accepted/pushed8 commits at98876fe; only C2 plan is draft planning, untracked:
plan/C2_TYPED_CONTEXT_PLAN.md, SHA256
0f308dacaf2422a31c3994a05adf4e4321af85f7995c8344e11da8190d367bb7.
The draft/inventory has not received a full Codex plan review; recommendations Q1–Q5
are not owner decisions. Keep original C1 approval/plan/evidence unchanged.

Complete local handover (absolute operator paths/package hashes, ignored) is in
the BE2-01 worktree: features/FEAT-044-be2-ai-job-foundation/evidence/local/claude/
handover/BE2_RESUME_ORDER_20261017.md. Use its current A17 ZIP/README, not an old R2 ZIP.

## C2 implementation —2026-10-17 (historical; superseded by the C2 review and owner acceptance)

User sent the genuine C2 approval (verbatim approvals/C2_TASK_APPROVAL.md; plan rev2 SHA256
4b339514…; Q1–Q5 as recommended). Claude implemented C2.1–C2.5 in this worktree only: trusted typed
snapshot gate, minimized `VisionTypedContextV1` projection, payload/context digests, 0.2-candidate
typed records, offline context adapter over an injected transport, current-context checks across
observation/replay/downstream/new corrections. Fresh run: C2 179/179, C1 focused + V2 server
240/240, legacy Vision 233 + 5 pre-existing skips, BE2-01 338/338; ruff/strict mypy and all
validators pass. Evidence evidence/notes/C2_IMPLEMENTATION_EVIDENCE_20261017.md; choices in
DECISIONS "C2 candidate technical choices"; handoff H_AI_REVIEW_HANDOFF.md C2 section.
Disposition C2_CODE_COMPLETE_PENDING_CODEX_REVIEW — stop for Codex review; no owner acceptance,
full-card DONE, runtime/model claim or Git action. BE2-01 stays WAITING_STUDIO; Lightning recovery
unconfirmed; if the user redirects to Studio, checkpoint C2 and follow the saved A17-fix01 procedure.

## C2 Codex review —2026-10-17 (historical; owner acceptance below is current)

CODE_REVIEW_PASS_WITH_NOTES / PENDING_OWNER_COMPONENT_ACCEPTANCE. No actionable new finding;
root657 collected/652 passed/5 pre-existing legacy skips, ruff/strict mypy PASS on16 paths,
adapter extra9/9. Same-family delegated area reviews found no blocker. Current gates and
limits: evidence/notes/C2_CODEX_REVIEW_20261017.md and matching metrics. Implementation records
above retain the pre-review stop. No source/test/approval changes, owner acceptance, card
closure or Git action by this review; BE2-01 remains WAITING_STUDIO.

## C2 owner acceptance —2026-10-17 11:59 +07:00 (current)

User accepted C2_TYPED_CONTEXT_OFFLINE in offline component scope on plan revision2 and
evidence/notes/C2_CODEX_REVIEW_20261017.md (verbatim approvals/C2_COMPONENT_ACCEPTANCE.md). Not full
BE2-02, production adoption, BE1/P1/P4 sign-off or real provider/model/runtime evidence; Codex
review notes stay open. Same message asked for an uncommitted-change inventory and a commit plan
only: evidence/notes/C2_PUBLICATION_PLAN_20261017.md (PROPOSED, for Codex review). No stage/commit/
push/merge/deploy and no next checkpoint. BE2-02 IN_PROGRESS/NOT_DONE; BE2-01 WAITING_STUDIO.

## C2 local publication —2026-10-17 12:38 +07:00 (current)

User approved executing the Codex-re-reviewed plan (4 commits / 37 files, 6/17/11/3) and allowed
staging and all four local commits. Before each commit: repository security validator exit 0,
explicit-path staging, staged set equal to the plan, staged blob bytes equal to working bytes and
to pinned evidence hashes, `git diff --cached --check` clean. Commits 52bf84f and 164575c are on the
branch; this records commit and the shared-ledger routing commit follow. Hashes of the last two and
the receipts are in ignored evidence/local/c2-publication-exec-20261017/. Not pushed; no merge/
deploy or next checkpoint. BE2-02 IN_PROGRESS/NOT_DONE; BE2-01 WAITING_STUDIO.
