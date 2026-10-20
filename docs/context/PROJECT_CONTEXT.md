# Project context ledger

## BE2-01–14 offline integration and runtime-readiness candidate — 2026-10-20

`feature/be2-backend-ai-integration` is the renamed local candidate branch; it
contains the merge at
`abe3c357e2c40c694317ead6cf9a1b7c479e3f6e`, combining task-7 tip
9d1ed184f31ab6b1f18337a1e29bb04fd59aa1b5 with receiver tip
42a6d3122259e6b33133673a2e444deefa45d387, preserving both histories. The task-7
PR target feature/be2-01-07 already points to the same task-7 commit, so that PR
is empty. Offline card runners pass for BE2-08, 09, 10, 11 and 13. BE2-12 and 14
remain blocked by the backend environment's missing python-multipart dependency;
476/477 BE2-12 cases pass, and BE2-14's 1,061 owned plus 114 foundation cases
pass. All seven card statuses remain IN_PROGRESS or IN_PROGRESS_PENDING_EXTERNAL;
real owner/runtime/provider and Lightning gates remain open. The reviewable
receipts are in FEAT-057 evidence. No live test has run. This is an offline
integration candidate, not card acceptance or a dev/main merge.

The owner then requested a cross-card BE2-01–14 runtime-readiness analysis for a
future Lightning recovery. FEAT-057's approved runbook maps each task's current
runtime gate and exact existing command. There is no safe one-shot 01–14 runtime
runner: only the frozen BE2-01 A17-fix01 Studio checkpoint has a prepared remote
procedure; real adapters/adoption remain missing across the shared workflow. The
branch has not been published, and Lightning/provider/database execution was not
performed during this analysis.

## BE2-07 offline component accepted — 2026-10-20

Person 2's conditional instruction ("Viết prompt cho claude review lần cuối đi nếu ok thì chấp nhận
đẩy lên nhánh gộp") applied after the final review PASS of FEAT-056 at 763a17c. Accepted:
KNOWLEDGE_SCRIPT_COMPONENT_OFFLINE only (FEAT-056 approvals/COMPONENT_ACCEPTANCE.md). The reviewed
snapshot is fast-forwarded onto feature/be2-01-07. Card IN_PROGRESS / NOT_DONE; Lightning/runtime,
real adapters, HTTP/DB, actual08 adoption/fence and cross-card integration remain open. 56-module
batch NOT_RUN on cloud; latest run is Codex's on the identical product tree.

## BE2-07 cloud P3 corrections — 2026-10-20

Approved follow-up closes invisible-character/CGJ and optimized-verifier P3 findings. Fresh
local56-module batch has1,660pass/3Pillow skip and42mapped IDs/506 passed references; independent
product/tooling reviews are recorded by FEAT-056. New current handoff uses POST_CLOUD_P3.
Raw cloud archive/conditional export cleanup are still pending; component NOT_ACCEPTED/card
IN_PROGRESS / NOT_DONE. Frozen plan/approval and runtime/Lightning boundaries remain intact.

## BE2-07 Git publication and Claude cloud review — 2026-10-20

The user authorizes a 12-commit publication of the reviewed task07 snapshot and a Claude cloud
review session on `feature/be2-07-knowledge-script`. FEAT-056 publication approval records the
superseding Git authority; frozen offline approval and plan remain unchanged. Portable review
evidence is published with provenance; local-only checks remain explicit. Component NOT_ACCEPTED,
card IN_PROGRESS / NOT_DONE; runtime/Lightning, owner acceptance and actual08 adoption stay open.

## BE2-07 approved offline execution — 2026-10-19

User approved FEAT-056 plan revision 1 and OD01–08. ACTIVE07/WIP1 on own task branch; 06 offline accepted, 01 WAITING_STUDIO. Execute eight parts and42 assertions to owner review-ready. Component NOT_ACCEPTED, card IN_PROGRESS/NOT_DONE. Runtime/integration and Git publication remain separate gates.


## BE2-07 offline planning after task06 merge — 2026-10-19

User requested the final lane task07 plan, offline first, and a later coordinated Lightning
runtime campaign01–07. Task06 PR15 is merged at23acf9e; its14commits/45files are preserved.
Ownbranch feature/be2-07-knowledge-script starts there; administrative FEAT-056 was unused
after freshfetch/48ref inventory. FEAT-056 plan revision 1 and OD01–08 await owner plan approval;
source/tests07 NOT_STARTED, no new implementation ACTIVE slot. Scope is sourced knowledge/
script/correction/current eligibility fixture component. Runtime missing adapters remain
NOT_IMPLEMENTED, A17Studio NOT_RUN; later campaign preserves exact frozenA17 profile.
No task07publication/runtime authorization or offlineacceptance inferred. Earlier entries
retain their dated checkpoint state. Source: FEAT-056 approvals/TASK_APPROVAL.md and plan/PLAN.md.


## BE2-06 offline component accepted — 2026-10-19

Person 2 accepted FEAT-055 CHILD_RESPONSE_COMPONENT_OFFLINE on Codex PASS_WITH_NOTES;
B6-CR01 closed, zero remaining known P1/P2 in reviewed offline scope. Acceptance is in
FEAT-055 approvals/COMPONENT_ACCEPTANCE.md. Card stays IN_PROGRESS / NOT_DONE; runtime and
integration remain open. Final offline batch: 1322 pass / 3 Pillow skips, including all 155
BE2-06 tests. The owner requested a commit plan for review only; no stage, task06 commit,
push, shared-branch update or merge authorized. Publication plan: FEAT-055
evidence/notes/BE206_PUBLICATION_PLAN_20261019.md. WIP1;07 PARKED;01 WAITING_STUDIO.
Earlier dated checkpoints and their NOT_ACCEPTED descriptions remain history.

## BE2-06 offline implementation ready for owner review — 2026-10-19

FEAT-055 CHILD_RESPONSE_COMPONENT_OFFLINE implemented on feature/be2-06-child-response at base818ec077; component NOT_ACCEPTED, card IN_PROGRESS/NOT_DONE. Final one-pass required01–06offline batch1322pass/3Pillow-skips/0failure-error (06=155pass), Ruff/strictmypy2modes/fourvalidators/diffcheckpass;558existingcode/testfiles unchanged. Independent review found/fixedB6-CR01P2 nestedfakecommit lostack; no remainingP1/P2 known in offline scope. Evidence/review/acceptance map and future runtime checklist in FEAT-055. No owneracceptance, newcommit/push/merge or runtimeclosure.07PARKED;01WAITING_STUDIO. Earlier dated checkpoints are history.

## BE2-06 offline execution — 2026-10-19

User directed Codex to write an execution prompt and use it to implement Rev5 locally. FEAT-055-be2-child-response owns CHILD_RESPONSE_COMPONENT_OFFLINE; fresh inventory found proposed054 occupied, so055 was selected administratively under that instruction (not an explicit user number quote). Single ACTIVE06/WIP1;07 PARKED;01 WAITING_STUDIO. Formal plan/approval precede code. Required offline final regressions will run on one completed snapshot; Lightning/runtime/integration remain open for a future batch. No Git publication approval.

## BE2-05 offline component accepted — 2026-10-19

Person 2 accepted `SKETCH_REVIEW_COMPONENT_OFFLINE` on Codex re-review
`CODEX_REREVIEW_PASS_WITH_NOTES` (0 P1/P2; RV-CR01–05 closed). BE2-05 remains IN_PROGRESS / NOT_DONE.
Runtime, production, SQL/durable persistence, BE1 authority/ticket, BE2-14 policy and integration
gates remain open. Acceptance: FEAT-052 `approvals/COMPONENT_ACCEPTANCE.md`. Person 2 separately
authorized the 20-group publication plan, the task-branch commits, and a fast-forward push to
`feature/be2-01-07`; see FEAT-052 `DECISIONS.md` and its local receipt for resulting SHAs. BE2-06
planning only follows publication; no BE2-06 implementation is authorized.

## BE2-05 Codex re-review - 2026-10-19

Independent re-review closed RV-CR01–05 with 0 P1/P2 remaining and passed the focused offline
checks. The component remains NOT_ACCEPTED pending owner acceptance; BE2-05 stays IN_PROGRESS /
NOT_DONE. Report: FEAT-052 evidence/notes/BE205_CODEX_REREVIEW_20261019.md. No commit, push or
merge; BE2-07 PARKED; WIP1.

## BE2-05 ACTIVE on its own task branch - 2026-10-19

Person 2 approved BE2-05 plan candidate R2 (SHA256 ab295305…) and allocated
**FEAT-052-be2-sketch-review** as the owner's own number decision (fresh inventory after fetch
found no FEAT-052; lane 08–14 confirmation waived, not claimed; collisions mapped at
integration). BE2-05 is the single ACTIVE slot (WIP1) by substitution while BE2-01 is
WAITING_STUDIO and BE2-04 live is unavailable; scope is the offline component only. Workflow is
now one branch per task (`feature/be2-05-sketch-review`, worktree `.worktrees/be2-05-sketch-review`,
from shared tip 58293f1); accepted checkpoints enter `feature/be2-01-07` only by a separate owner
Git decision. This supersedes coding 02–07 directly on the shared branch. BE2-07 PARKED; BE2-06
backlog. Records: FEAT-052 approvals/TASK_APPROVAL.md and DECISIONS.

## Shared BE2 branch routing publication - 2026-10-19

Person 2 authorized Codex to publish the six routing documents as one documentation commit on
`feature/be2-01-07` and push that branch with upstream, then write a local Claude handover.
Baseline is the accepted/pushed SK1 tip 6ab7abf. Authorization and scope are recorded in FEAT-050
DECISIONS and SOURCE_REGISTER; execution receipt/final tip in FEAT-050 ignored
`evidence/local/shared-routing-publication-20261019/receipt.json`. WIP1 remains; the next ACTIVE
card, feature-number allocation and integration checkpoint are undecided. BE2-01 WAITING_STUDIO,
BE2-02 PARKED, BE2-03/04 IN_PROGRESS with their recorded offline component acceptances.

## BE2-01–07 shared working branch —2026-10-19

Owner direction (Person 2): shared working branch `feature/be2-01-07` created 2026-10-19 00:15 +07:00 from the
accepted and pushed BE2-04 SK1 tip 6ab7abf (worktree `.worktrees/be2-01-07`; local, not
pushed). It inherits BE2-01–04; older card branches stay as milestones. Next work and fixes for
02–07 go on this branch in their owning features; WIP1 with per-card plan/approval/evidence/
review/acceptance/commit groups; BE2-01 fixes arrive from the frozen A17 track by reviewed SHA.
SK1 accepted offline and pushed (ba93c20..6ab7abf); no card DONE; next ACTIVE card, FEAT
allocation and integration checkpoint undecided (FEAT-050 DECISIONS). BE2-01 WAITING_STUDIO;
BE2-02 PARKED; BE2-03/BE2-04 IN_PROGRESS. Earlier entries are history.

## BE2-04 SK1 component acceptance —2026-10-18

Owner accepted BE2-04 SKETCH_COMPONENT_OFFLINE (SK1) at 23:15 +07:00 on the snapshot matching the
final Codex focused review (FEAT-050 approvals/SK1_COMPONENT_ACCEPTANCE.md). Dispositions: F-5
fixture-composition deviation accepted; N04/N08/N11 chain and C03/C03b contract column PARTIAL;
A1 callback end to end NOT_RUN (future integration gate); N16 fixture residual accepted. Offline
component scope only: BE2-04 IN_PROGRESS / NOT_DONE; no runtime claim. Uncommitted; publication
plan FEAT-050 evidence/notes/SK1_PUBLICATION_PLAN_20261018.md awaits owner review. BE2-01
WAITING_STUDIO; BE2-02 PARKED; BE2-03 A1 accepted offline / card IN_PROGRESS. Earlier entries are
history.

## BE2-03 A1 component acceptance —2026-10-17

Latest: Owner approved the corrected publication plan (FEAT-049 evidence/notes/A1_PUBLICATION_PLAN_20261017.md, SHA256 1065fa3f…; amended by owner instruction to a01e8527… to keep 4 reviewed CRLF metrics byte-exact via .gitattributes, 64 paths) on 2026-10-17 23:42 +07:00 for four local commits C1–C4, with the repository security validator run before each commit; not pushed (push needs a separate instruction after re-checking the actual remote tip).

Owner accepted BE2-03 A1 ASSISTANCE_COMPONENT_OFFLINE at 23:24 +07:00 on the final Codex review
(FEAT-049 approvals/A1_COMPONENT_ACCEPTANCE.md). Offline component scope only: not full-card,
production adoption or other owners' sign-off. BE2-03 IN_PROGRESS / NOT_DONE; BE2-02 PARKED;
BE2-01 WAITING_STUDIO. Work is uncommitted; publication plan FEAT-049
evidence/notes/A1_PUBLICATION_PLAN_20261017.md awaits owner review. Earlier entries are history.

## BE2-03 A1 final code review —2026-10-17

Latest: **A1_CODE_REVIEW_PASS_PENDING_OWNER_ACCEPTANCE**. CODE_REVIEW_PASS, 0 P1 / 0 P2;
original CR01–CR05 and residual CR03-F1/F2 closed at A1 offline scope. Root 878/878 pass,
0 skip (128 A1 + 338 foundation + 412 Vision). FEAT-049
evidence/notes/A1_CODEX_FINAL_REVIEW_20261017.md and metrics bind the result to source hashes.
No owner acceptance/publication/runtime closure recorded; BE2-03 IN_PROGRESS / NOT_DONE,
BE2-02 PARKED, BE2-01 WAITING_STUDIO. Earlier entries below are history.

## BE2-03 A1 Codex fix re-review —2026-10-17

Latest: **A1_NEEDS_REVISION_AFTER_FIXES** (0 P1 / 2 P2). Root 868/868 offline tests pass,
0 skip; two residual CR03 cases reproduce: same-thread publication inside assistance commit
and Vision invalidation outside the decision epoch. FEAT-049
evidence/notes/A1_CODEX_REREVIEW_20261017.md and metrics hold the review. Next: fixes and
re-review within existing A1 approval. No component acceptance/publication; BE2-03 NOT_DONE,
BE2-02 PARKED, BE2-01 WAITING_STUDIO. Earlier checkpoints below are history.

## BE2-03 A1 implementation —2026-10-17

Latest: A1-CR03-F1/F2 (re-review 0 P1 / 2 P2) fixed under the existing A1 approval; A1 128/128,
BE2-01 338/338, BE2-02 412/412, 0 skips; pending Codex re-review (FEAT-049
evidence/notes/A1_CR03_FOLLOWUP_EVIDENCE_20261017.md). Uncommitted; not accepted.

Latest: A1-CR01–CR05 fixed under the existing A1 approval (regressions first); A1 118/118,
BE2-01 338/338, BE2-02 412/412, 0 skips; A1_FIXES_COMPLETE_PENDING_CODEX_REREVIEW (FEAT-049
evidence/notes/A1_REVIEW_FIX_EVIDENCE_20261017.md). Uncommitted; not accepted.

Latest Codex review: A1_NEEDS_REVISION (0 P1 / 5 P2; FEAT-049
evidence/notes/A1_CODEX_REVIEW_20261017.md). Root851/851 offline regressions pass;
targeted probes reproduce five code issues. Next: fixes within existing approval,
regressions and re-review. No component acceptance or Git publication. Earlier
implementation checkpoint below is history.

Owner approved BE2-03 A1 ASSISTANCE_COMPONENT_OFFLINE on plan revision 3 (SHA256 e1fce645…,
D1–D11 as recommended) at 19:58 +07:00; verbatim FEAT-049 approvals/TASK_APPROVAL.md. Claude
implemented A1.1–A1.5 offline (new modules only; no foundation/Vision edits): state
A1_CODE_COMPLETE_PENDING_CODEX_REVIEW, A1 101/101, BE2-01 338/338, BE2-02 412/412, 0 skips.
Not component acceptance, runtime, real provider or full-card DONE; uncommitted. BE2-02 parked
at accepted C2; BE2-01 WAITING_STUDIO. Evidence: FEAT-049
evidence/notes/A1_IMPLEMENTATION_EVIDENCE_20261017.md. The planning entry below is history.

## BE2-03 planning —2026-10-17

FEAT-049 maps BE2-03 assistance request/cancel/dedup/cache/budget orchestration on candidate
branch feature/be2-03-assistance-orchestration, stacked on the pushed BE2-02 C2 checkpoint
f120c4f (not dev). Plan revision 1 (ASSISTANCE_COMPONENT_OFFLINE) is AWAITING_APPROVAL;
Codex review NEEDS_REVISION (1 P1 / 4 P2; FEAT-049 evidence/notes/PLAN_CODEX_REVIEW_20261017.md).
Revision 2 (SHA256 0894c39b…) re-review NEEDS_REVISION (0 P1 / 1 P2): only explicit fake
commit-boundary coordination remains (FEAT-049 PLAN_CODEX_REREVIEW_20261017.md).
Revision 3 (SHA256 e1fce645…) final review PLAN_REVIEW_PASS; all plan findings closed
(FEAT-049 evidence/notes/PLAN_CODEX_FINAL_REVIEW_20261017.md). Next: real owner approval
of this revision/hash and D1–D11 before A1.1–A1.5 implementation. No choice selected here.
No code or Git publication; BE2-01 WAITING_STUDIO
and BE2-02 IN_PROGRESS/NOT_DONE unchanged. Links: features/FEAT-049-be2-assistance-orchestration/.

## BE2-02 current state —2026-10-17

Owner accepted C2_TYPED_CONTEXT_OFFLINE (offline component scope) on 2026-10-17 11:59 +07:00,
verbatim FEAT-048 approvals/C2_COMPONENT_ACCEPTANCE.md, on CODE_REVIEW_PASS_WITH_NOTES
(evidence/notes/C2_CODEX_REVIEW_20261017.md: root652 pass/5 pre-existing legacy skips, no actionable
finding). Not full BE2-02/production/BE1-P1-P4 sign-off/real runtime. The re-reviewed plan
evidence/notes/C2_PUBLICATION_PLAN_20261017.md (37 files) was executed locally 2026-10-17 as four
commits 52bf84f, 164575c, c601658 and this routing commit; not pushed. The implementation
checkpoint below is historical to this acceptance.

User approved C2_TYPED_CONTEXT_OFFLINE on 2026-10-17 11:20 +07:00 (plan revision2 SHA256
4b339514…, Q1–Q5 as recommended; verbatim FEAT-048 approvals/C2_TASK_APPROVAL.md). Claude
implemented C2.1–C2.5 offline; state C2_CODE_COMPLETE_PENDING_CODEX_REVIEW, uncommitted. Fresh
checks: C2 179/179, C1 + V2 server 240/240, legacy Vision 233/5 pre-existing skips, BE2-01
338/338; validators pass. Card IN_PROGRESS/NOT_DONE; no owner acceptance, runtime/model claim or
Git action. BE2-01 WAITING_STUDIO; Lightning recovery unconfirmed. C1 was pushed at98876fe.
Earlier dated routing/publication statements below are history. Current sources: FEAT-048
CONTEXT/status and evidence/notes/C2_IMPLEMENTATION_EVIDENCE_20261017.md.

FEAT-048 maps BE2-02 Vision and meaning correction on feature/be2-02-vision-correction
(candidate base 6dcc57e). Planrev1 C1_COMPONENT_OFFLINE was approved
19:18 +07:00 and accepted by the owner 21:26 +07:00 after Codex review (C1-R01–R06 closed,
PASS_WITH_NOTES) and final verification (focused 233 + V2 server 7 + foundation route 1 passed,
0 skips). Component scope only: BE2-02 IN_PROGRESS/NOT_DONE; N01, legacy F-01, typed provider
context, real model/quality, BE1/BE2-03 adapters, persistence/delivery and live integration
remain open. BE2-01 stays WAITING_STUDIO (CR01 open, B-12 HANDOFF); no C2 or other card opened.
Publication: 7 local commits 0f75fa5..af47ecc (68 files) plus a status-sync docs commit; not pushed.
Links (features/FEAT-048-be2-vision-correction/): status/STATUS.md, approvals/TASK_APPROVAL.md,
approvals/C1_COMPONENT_ACCEPTANCE.md, evidence/notes/C1_FINAL_VERIFICATION_20261016.md,
evidence/notes/C1_CODEX_R04_CLOSURE_20261016.md, evidence/notes/H_AI_REVIEW_HANDOFF.md,
evidence/notes/C1_PUBLICATION_PLAN_20261016.md; full step history in evidence/README.md.

## BE2-10/11/13 actual own PostgreSQL —2026-10-19

Parent2d5d925; actual owner "duyêjt" approves proposed42 tests/isolated temporary
environment/scoped fixes/cleanup/report/commit. Separate approvals +environment
plans recorded in FEAT-052/053/054 BEFORE setup; frozen main plans unchanged.
Fresh portable PG17.11/SCRAM/loopback only, three NEW prefixed databases owned by
separate nonsuperuser/nocreatedb/nocreaterole/noreplication roles. Exact actual native
version/address/data_directory/role checked; no shared URL/service/PATH or provider.
Actual10 SQL14/14,11 SQL17/17,13 SQL11/11 =>42 PASS,0 fail/error/skip; exact node/
JUnit and837 source closure unchanged. First actual run passed; no application/
migration/test fixes or SQL pin changes needed. Exact own cluster/binaries/archive/
secrets/private server log removed,0 own processes/old-port listeners. Retained
sanitized receipts only. Post-cleanup194+2849=3043 local PASS,830 sources unchanged,
Ruff/Mypy11/architecture/harness/security/diff PASS. E02 +ACTUAL_POSTGRES metrics
in each feature. Local runners' SQL COLLECTED_NOT_RUN remains their intentionally
SQL-disabled receipt, NOT current actual gate status. Own SQL complete for these
cards, full cards still pending actual source/policy/BE1/P4/native owner adoption/
combined acceptance. No actual model/Lightning/provider/production mount/push/merge.

## BE2-13 approved internal completion —2026-10-19

Implementation parent448e41f; owner direct "duyệt" approves FEAT-054 revision1
P1–P4, frozen601afab8 plan unchanged. Immutable preset versions/strict12 delegate/
old-version recall and exact pin/control intents, bounded evaluator/decisions/pure
admission, Teacher override/disable/native receipt/no-new-effect reconcile ports,
own CAS/history/codec/frozen migration, narrow existing CMD-48 safe error mapping,
local runner and three receiver handoffs complete.194 own +2849 prior=3043 PASS,
0 skipped/errors/failures;829 sources unchanged; Ruff/Mypy11/architecture/harness/
security/diff PASS. Own11 PG COLLECTED_NOT_RUN; separate environment approval.
Internal COMPLETE_LOCAL_VERIFIED; full13 IN_PROGRESS_PENDING_EXTERNAL. Actual
CR13-01/02/03 preset/current policy/BE1 atomic effects/epochs/dedup/native reconcile/
scheduler/P4 and combined acceptance OPEN; teammates wire later per owner. No actual
provider/Lightning/SQL provisioning/production mounting/push/merge/deploy. Last
internally unstarted receiver card implemented; earlier external gates and10 SQL14/
11 SQL17 NOT_RUN not waived. FEAT-054 E01 and artifacts current, planning below historical.

## BE2-13 next-card planning —2026-10-19

Owner "task tiếp theo" after11 internal checkpoint f821cc2: inspect/plan only.
FEAT-054 revision1 P1–P4 AWAITING_APPROVAL/NOT_STARTED: typed versioned preset
delegate via sole12 CMD-48; immutable pin references and bounded automation intents;
Teacher override/disable through BE1 atomic command/receipt/recovery port; own SQL
preparation and complete local audit/handoff. FR053/054 detail/priority remain
candidate, no hidden policy adoption. CR13-01/02/03 actual preset/current session/
scheduler contracts OPEN; no actual SQL/provider/BE1/P4/production effects. Present
exact approval next.11 own17 SQL NOT_RUN/actual integration gates not waived.

## BE2-11 approved internal completion —2026-10-19

Parent261d00a; owner direct "duyệt" approves FEAT-053 revision1 P1–P4. Frozen
09348e0f plan unchanged. Reviewed definition/publication join +broad topic/exact-age
discovery/optional ranker bridge; immutable local group adaptations; six guarded
Teacher actions/per-child preparation/current policy ports; own CAS/history/receipts/
terminal outcome attribution+ACK/codec/frozen migration; injected CMD-45/CMD-59
source provider and full receiver handoff delivered. Final219 own +2605 regression
+25 legacy=2849 PASS,0 skips;806 sources unchanged, Ruff/Mypy12/governance/security/
diff PASS. Own17 PG COLLECTED_NOT_RUN, separate environment approval needed.
Internal COMPLETE_LOCAL_VERIFIED; full11 IN_PROGRESS_PENDING_EXTERNAL. CR11-01/02/03
actual source assets/current policy/fences/BE1/P4 composition/result dedup/save/ACK
and actual integrated acceptance OPEN; teammates wire later. No provider/Lightning/
SQL provisioning/production mount/push/merge/deploy or13 activation. FEAT-053 E01
and three artifacts are current handoff; older planning checkpoint below historical.

## BE2-11 next-card planning —2026-10-19

Owner "task tiếp" after10 internal checkpoint7b49a1b authorizes inspect/plan only.
FEAT-053 revision1 P1–P4 AWAITING_APPROVAL/NOT_STARTED: broad reviewed discovery,
local immutable Teacher/group adaptation, per-child policy/preparation execution,
six actions/CAS, own storage/CMD-45 +BE1 catalog/outcome consumer handoff and audit.
No copied legacy readiness/material hardfilter; FR042/043/reflection refinements
still candidate. CR11-01/02/03 actual definition/policy/BE1 adapters OPEN. No code/
SQL/provider/production mount or13 activation. Present exact plan approval next;
10 SQL14 still NOT_RUN, no evidence/adoption/provisioning authority inherited.

## BE2-10 approved internal completion —2026-10-19

Parent b8910dc; direct owner "duyệt" approves exact FEAT-052 revision1 P1–P4. Recorded
approval before code, frozen8d0162c6 plan unchanged. Exact exhaustion/three choices,
bounded retry proof, unique claim/intent-first service/receipt recovery, own SQL/
codec/migration, injected CMD-43 and consolidated local runner/handoff/audit complete.
253 own +2352 existing=2605 PASS,0 skipped,753 source closure unchanged, Ruff/Mypy10/
architecture/harness/security/diff PASS.14 actual PG prepared/collected only NOT_RUN.
Internal COMPLETE_LOCAL_VERIFIED, full10 IN_PROGRESS. Actual failure/new lifecycle/
budget consume/session-checkpoint/late-result/reconciliation CR10-01/02/03 and owner
acceptance OPEN.08 same-pin semantic uniqueness requires adopted retry-aware path,
not terminal reset/create reuse. No SQL provisioning/provider/Lightning/production
mount/push/merge/11/13 activation. Current FEAT-052 E01 +three artifacts/metrics.

## BE2-10 next-card planning —2026-10-19

Owner "tiếp" after total report routes planning only. Baseline76959ab, clean
feature/be2-08-14. FEAT-052 revision1 P1–P4 prepared AWAITING_APPROVAL/NOT_STARTED:
exact exhausted target +bounded Teacher retry/new lifecycle, skip, early-end with
checkpoint, guarded recoverable intent/receipts, own SQL/HTTP and consolidated
verification/handoff. CR10-01/02/03 candidate adoption OPEN. No code/runtime/SQL
provisioning or new numeric policy; plan presentation/exact approval next.09 own
SQL21/local458 evidence retained separately; actual integration still deferred.

## BE2-09 C4b actual own PostgreSQL —2026-10-18

Parent1ce8d07; separate direct owner "duyệt" approves temporary local PG17, exact21
SQL cases/scoped fixes/cleanup/checkpoint. Recorded FEAT-051 local approval/plan
before setup. Actual21 PASS,0 failure/error/skip, PG17.11 loopback nonsuperuser,
733 source files unchanged, no code fixes. Exact cluster/binaries/archive/secrets
removed; no remaining PG process. Own SQL gate now PASS; local pack stays deliberate
collection-only, not a retraction of separate E07 actual evidence. Internal complete,
full09 IN_PROGRESS pending actual CR09-01/02/BE1 access/session/owner/runtime quality
acceptance. No shared/prod DB, global service/install, provider/Lightning, push/merge.

## BE2-09 C4 internal completion —2026-10-18

Parent b0983a0; owner explicitly approves finishing remaining INTERNAL P3/P4 in one
run. HTTP CMD-41/42 candidates,117 HTTP +22 runner new tests and consolidated
handoff/audit delivered.458 own +1894 existing=2352 PASS, no skips;731 transitive
source closure unchanged/exact pinned nodes+JUnit; Ruff/Mypy17/governance/security
PASS. Internal COMPLETE_LOCAL_VERIFIED, full09 IN_PROGRESS.21 PG tests prepared/
collected only NOT_RUN. Actual canonical08/09 head +BE1 current session/access/
gateway adoption CR09-01/02 OPEN, selected08 runtime/quality/consumer acceptance
pending. No internal checkpoint needs another "tiếp"; no automatic10 implementation,
SQL/provider/Lightning activation or push/merge/deploy. Current FEAT-051 E06 and
artifacts/LOCAL_VERIFICATION_HANDOFF.md, HTTP_CONTRACT_HANDOFF.md, ACCEPTANCE_AUDIT.md.

## BE2-09 C3a owned persistence component —2026-10-18

Parent09a707b, approved FEAT-051 revision1 unchanged. Own video_review closed codec/
six-table schema/SQL UoW adapters/new branch migration, no08/BE1 shared-row writes.
70 new mock/offline cases,319 own +1894 existing=2213 PASS,669 backend source files
unchanged; Ruff/Mypy15 PASS.10 actual PG17 tests prepared/collected only NOT_RUN,
separate VR09 environment authorization required. P3 injected HTTP/P4 next, actual
canonical head/access/session/revocation adoption CR09-01/02 OPEN. Full09 remains
IN_PROGRESS. Current E05; no DB/provider/Lightning activation or push/merge.

## BE2-09 C2b lifecycle/rebind component —2026-10-18

Parent01b4be9, approved FEAT-051 revision1.60 new/249 own +1894 existing=2143 PASS,
662 backend source files unchanged, Ruff/Mypy11 PASS. Invalidation/archive +new
empty review head across version/context/audience changes; same-content restoration
requires fresh review, no approval revival. Actual source-owner/canonical head/
access revocation CR09-01/02 adoption OPEN. P3 storage/HTTP and P4 next; current
FEAT-051 E04. Full09 IN_PROGRESS, no SQL/provider/Lightning activation.

## BE2-09 C2a guarded review-write component —2026-10-18

Parent cd942dd; FEAT-051 approved revision1 unchanged. Review-write/current snapshot/
atomic own UoW candidate ports/service with current replay applicability.53 new/
189 own +1894 existing=2083 PASS;658 backend source files unchanged, Ruff/Mypy8 PASS.
Actual owner/canonical head/version rebind/SQL/HTTP/access adoption still open,
no automatic playback or2083-as-integration claim. P3/P4 pending; current FEAT-051
E03. Full09 IN_PROGRESS, no provider/SQL/Lightning activation.

## BE2-09 C1b playback intent/recovery component —2026-10-18

Parent aa10fe5, approved FEAT-051 revision1 unchanged.52 new/136 own +1894 existing
=2030 PASS,655 backend source files unchanged, Ruff/Mypy6 PASS. Intent-first
guarded start/original-key receipt recovery component, no resend/URL/fake current
playing grant. Actual authority/store/BE1 session/access/receipt/fetch adoption
CR09-01/02 OPEN. P2 review-write/P3 persistence-HTTP/P4 verification next, full09
IN_PROGRESS. Current FEAT-051 E02; no provider/SQL/Lightning activation.

## BE2-09 approved revision1 / C1a —2026-10-18

Owner "duyệt" approves FEAT-051 P1–P4 exact revision1 after presentation. Parent
1ab9498; frozen plan unchanged. Shared24 video/session consumer +pure exact review
head/audience/invalidation component:84 own/1978 broad PASS,651 backend source
files unchanged; Ruff/Mypy3 PASS. No authority/access/HTTP/SQL effects, actual
CR09-01/02 remain open. P1 playback/P2–P4 next. Full09 IN_PROGRESS;08 runtime and
teammate integrations still deferred, no provider/Lightning activation.

## Receiver BE2-09 planning / delayed runtime batch —2026-10-18

Owner approves moving to next-card planning and batching Lightning later; baseline
07159ce. FEAT-051 revision1 P1–P4 prepared AWAITING_APPROVAL/NOT_STARTED. Shared24
reused; canonical09 review head/projection CR09-01 and BE1 session/access receipts
CR09-02 OPEN. No implementation/runtime activation.08 local/SQL PASS retained,
actual08/09 adoption/runtime not waived or marked DONE. Exact plan approval next.

## BE2-08 C4b actual own PostgreSQL11 PASS —2026-10-18

Parent c7b17ac; separate direct08 environment approval recorded before setup.
Actual PG17.11 own11 PASS, zero failure/error/skip;702-file source closure unchanged.
Loopback restricted runner, unique cluster/data/binaries/archive/secrets removed,
private receipts retained. No source fixes/provider/actual bridge activation.
FEAT-050 E09 and ACCEPTANCE_AUDIT.md: own SQL gate complete, actual foundation/
BE1/07/14/copy/runtime adoption open; whole08 IN_PROGRESS.

## BE2-08 C4 local verification/handoff —2026-10-18

Parent d55e9ca, FEAT-050 approved revision1 unchanged. One-command exact-node/
source-pinned runner, real authored GIF full-frame fixtures/rights, acceptance audit
and undecided runtime sheet available.459 own +1435 existing=1894 PASS;702-file
source closure unchanged; Ruff/Mypy19/governance PASS. SQL11 collected NOT_RUN;
production decoder/generation/actual adapters still open, whole08 IN_PROGRESS.
Current FEAT-050 artifacts/LOCAL_VERIFICATION_HANDOFF.md and ACCEPTANCE_AUDIT.md,
evidence/notes/C4_LOCAL_VERIFICATION_20261018.md. No activation/push/deploy.

## BE2-08 C3b provider-copy component —2026-10-18

Parent e21c7dd, FEAT-050 approved revision1 unchanged. Original-copy metadata and
guarded video hook consume14 exact envelope; no deletion authority/provider choice.
48 new/422 own, broad1857 PASS; Ruff/Mypy19 PASS,643 backend source files unchanged.
Actual journal/registration/source/authority/provider adoption OPEN; no actual
generation/SQL/deletion run. Next owned P4 runner/decoder pack/audit; whole08 still
IN_PROGRESS. Current handoff/evidence: FEAT-050 evidence/notes/C3B_PROVIDER_COPY_20261018.md.

## BE2-08 C3a worker/finalization component —2026-10-18

Owner says continue08; parent9d2677d, FEAT-050 revision1 unchanged. Worker admission,
private stage/finalization ports, scoped receipt checks and lost-ACK recovery now
component-implemented.45 new/374 cumulative own; broad1809 PASS,639 backend source
files unchanged; Ruff/Mypy16 PASS. Actual atomic start/completion/staging/cleanup
adapters remain open CR08-01; cleanup only pending, accepted references must be
protected atomically by actual adopter. No provider/SQL/runtime activation or
production registration. P3 partial, provider-copy/adoption and P4 runner remain;
whole08 IN_PROGRESS. Current FEAT-050 C3A_WORKER_FINALIZATION_HANDOFF.md.

## BE2-08 direct continuation / C2c —2026-10-18

Owner says continue08 in same chat; existing FEAT-050 revision1 applies. No new
goal/thread or original12 scope mutation. At parent b06b8a8, own explicit media
strategy/source/profile/decoder ports + validation and preparation implemented:
73 new/329 own, broad1764 PASS;636 backend source inventory unchanged, Ruff/Mypy14
PASS. No PATH ffmpeg/ffprobe; actual decoder/provider/SQL NOT_RUN. No production
defaults, completion/approval/artifact exposure or P5 activation inferred. Next P3
worker/finalization/copy and actual bridge/adoption; FEAT-050 C2C handoff is current.

## Original BE2-12 goal revalidation —2026-10-18

At16712de, owner objective attachment reread: original goal remains12, separate
08/14 work not credited to it. Current source-pinned477 component PASS and51
AI-policy HTTP binder PASS; source unchanged, full_goal_complete false. AI-policy
delegate now exists from14; actual preset/core/BE1 authority/consumer adoption and
integrated closure remain open, BE1/P4 deferred. No new SQL/app mount/08 work.
See FEAT-048 evidence/notes/C5B_CURRENT_GOAL_AUDIT_20261018.md.

## Receiver BE2-08 C2b HTTP/storage component —2026-10-18

FEAT-050 approved revision1 unchanged; parent9292bad. Injected candidate CMD-40
HTTP with closed native DATA-27 snapshot, own transaction-bound row participant,
strict codec and independent frozen knowledge_video migration. No production
registration/default auth/actual foundation job bridge/provider activation.
256 own +1435 existing=1691 PASS (48 suites,23 existing warnings); Ruff/Mypy11 PASS.
Actual PostgreSQL11 prepared/collected NOT_RUN, no provisioning/DB writes.
P2 remains partial (strategy surfaces/use cases, actual bridge adoption/evidence);
P3/P4 and P5 runtime remain. FEAT-050 C2B_HTTP_STORAGE_HANDOFF.md has current gates.

## Receiver BE2-08 C1/C2a component —2026-10-18

Approved FEAT-050 revision1 plan retained. Approval1ea7b53, C1 a3946e7;
owned strict CMD-40/DATA-27/domain plus C2a guarded create/lease/submission ports
and explicit fixture intents:164 own +205 selected regression=369 PASS,
Ruff/Mypy7 PASS. P2 partial; own persistence/HTTP and actual atomic foundation
bridge outstanding (CR08-01); P3/P4 not yet implemented, actual P5 separately
gated. No real07/BE1/policy/provider/SQL adoption or live route inferred. See
FEAT-050 status/STATUS.md and artifacts/CR_ATOMIC_VIDEO_SUBMISSION.md.

## Receiver BE2-08 approval —2026-10-18

Owner direct reply "duyệt làm task 08" approves FEAT-050 revision1, SHA256
370c6c04573a684c0e51c0ef1c276224d8e1f01ecd701624b2d925751cfa0b04,
P1–P4/P5 preparation and local checkpoint commits. Implementation IN_PROGRESS;
actual provider/profile/provisioning/SQL environment activation separately gated.
No push/merge/deploy. Reviewed plan bytes retained; earlier pending entries historical.

## Receiver BE2-08 planning —2026-10-18

Owner asked next task then "tiếp" after next-card planning proposal. Baseline
be64b99, feature/be2-08-14; FEAT-050 revision1 AWAITING_APPROVAL, implementation
NOT_STARTED. Follows12→14→08 receiver handoff order. Dedicated07 implementation
not located in current checkout; DATA-26/27 ShapeSpec candidates do not prove
adopted upstream runtime. Proposed P1–P4 owned component and P5 runtime preparation;
actual provider/profile/rights/provisioning/SQL environment separately gated.
No historical Wan/L4/duration/TTS selection inferred. Real BE1/P4 wiring remains
teammate-owned/deferred,12/14 not full integrated DONE. Entry: FEAT-050 plan/PLAN.md.

## Receiver BE2-14 actual PostgreSQL104 PASS —2026-10-18

Separate direct owner approval now permits local isolated PG17/test/cleanup for
BE2-14 only. Parent0e192da plus report-test helper unpack correction. Actual
PostgreSQL17.11 four packs15/10/21/58 all PASS,104 total zero failure/error/skip,
source unchanged. Initial copy56 PASS/2 FAIL retained, wrong helper unpack fixed,
all104 rerun. Cluster/data/binary/archive/secrets removed, private logs preserved.
Own SQL gate completed; earlier BE2-14 PG NOT_RUN counts below historical. Real
authority/registry/provider/telemetry/kill-generation adapter and consumer acceptance
still open, no full-card/original-goal DONE. BE1/P4 integration still deferred.
Evidence: FEAT-049 evidence/notes/C6D_LOCAL_POSTGRES_20261018.md.

## Receiver BE2-14 C6b health/queue component — 2026-10-18

Current feature/be2-08-14, parent a561128. Own health/queue projection gap found by
C6a now component-addressed: scoped typed producer/source binding, freshness/expiry,
fixture/runtime labels, null unknown vs actual0, no raw logs or foreign table scan.
Collector outside own transaction, expiry after transaction exit/current rights
rechecked. Local pack1061 own +114 foundation +477 regression/all64 source checks;
actual source/privacy/health/TTL adoption and stop-generation/provider/current-owner
integration still open. PG104 NOT_RUN, no provisioning/provider/production defaults.
BE2-12 real BE1/P4 integration remains owner-deferred and original goal not DONE.
Current handoff: FEAT-049 artifacts/H_OPERATIONS_TELEMETRY_HANDOFF.md and updated
ACCEPTANCE_AUDIT_20261018.md/CONSOLIDATED_TEST_HANDOFF.md. Earlier counts historical.

## Receiver BE2-14 C6a audit — 2026-10-18

Current receiver feature/be2-08-14, C6a parent e792512. BE2-14 revision1 approval
unchanged, full local pack1028 own +114 targeted foundation +477 selected regression,
all61 policy source Ruff/Mypy PASS. PostgreSQL104 prepared NOT_RUN, no card-local
server/provider activation or inferred provisioning authority. Acceptance audit
found remaining own safe health/queue projection work; policy/resource/copy reports
do not complete that backlog requirement. Next implement that own typed surface,
then conformance/audit. Stop-generation foundation CR and real owner/provider/BE1/P4
adoption remain open. BE2-12 component handoff/prior33 SQL evidence unchanged, real
integration owner-deferred and original goal NOT DONE. Current evidence/commands:
features/FEAT-049-be2-ai-policy/artifacts/ACCEPTANCE_AUDIT_20261018.md and
CONSOLIDATED_TEST_HANDOFF.md. Earlier snapshot counts below are historical.

## Receiver next-card planning — 2026-10-17

Latest: owner approved BE2-14 revision 1/P1–P5 by direct reply "duyệt"; approval
commit da38618, FEAT049 now IN_PROGRESS. C1 strict policy contracts/pure lifecycle
has 124 own component PASS and 477 existing selected regression PASS. SQL/runtime
activation and real owner/provider integration NOT_RUN. Production values/provider
choices/provisioning are not inferred. Earlier pending-plan statements below are
historical. Reviewed plan bytes/hash remain unchanged.

Receiver branch is now feature/be2-08-14 (owner-requested local rename). BE2-12
component/owned SQL checkpoint 6931daa and integration-deferral handoff f0ff7a8
are available; owner leaves real BE1/P4 wiring to teammates. This is not full
integrated acceptance. Owner now requests the next task: FEAT-049 BE2-14 plan
revision 1 is AWAITING_APPROVAL, implementation NOT_STARTED. Existing BE2-12 or
foundation approvals do not authorize new policy/provisioning/provider choices.
Sender 01–07 allocation and foundation's unresolved integration gates unchanged.
Entry: features/FEAT-049-be2-ai-policy/plan/PLAN.md.

## BE2 checkpoint publication and 7/7 handoff —2026-10-16

User authorized splitting and pushing the current BE2 checkpoint so the second BE2 executor can
fetch it and create a separate task branch. This publishes the reviewed A17-fix01 correction and
received cloud evidence, not a BE2-01 closure or dev merge. Current checkpoint:
**Q01/B6_A17FIX01_CLOUD_RECEIPTS_VERIFIED_PENDING_STUDIO**; cloud221 B2–B6 +224 Phase A PASS,
43/43 required durable PASS; Studio A17-fix01 NOT_RUN; BE2-01 IN_PROGRESS; B-12 HANDOFF;
OwnerFence ASSUMED_CONTRACT. Phase A/Phase B approvals are unchanged.

Allocation: existing executor **BE2-01–07**, second executor **BE2-08–14**. The latter starts
with BE2-12 planning and receives knowledge/script from sender-owned BE2-07. Default implementation
WIP remains1; this publication does not activate another implementation card. A candidate BE2-12
branch may be based on the fetched foundation feature checkpoint while dev lacks it; record that
base and remaining Studio/integration gates. Normal reviewed-card integration through dev remains.
Entry point: `features/FEAT-044-be2-ai-job-foundation/artifacts/BE2_08_14_TEAMMATE_HANDOFF.md`.
Detailed evidence: FEAT-044 `evidence/notes/PHASE_B_B6_A17FIX01_CLOUD_RECEIPT_REVIEW_20261016.md`.
Older dated execution entries below retain their historical state.

## BE2 current execution handoff —2026-10-16

- Latest 2026-10-16: BE2-01 stays at **Q01/B6_CR01_R2_CODE_PACKAGE_REVIEW_PASS_PENDING_RUNTIME** (Codex code/package review PASS on manifest cb527d7f; Studio runtime r2 NOT_RUN; B6-CR01 open). Person 2 allowed local checkpoint commits of the reviewed state before the Studio run (FEAT-044 DECISIONS 124); this is not acceptance. Earlier:

FEAT-044 B5 closed after exact fix03 reported runtime and independent closure review.
Existing owner O-09 Phase B revision 3 B1-B6 approval remains in force; candidate directives
remain PROJECT_OWNER_DIRECTIVE, not P1/P2/P4 role sign-off.
- Updated 2026-10-16, Asia/Saigon. Phase A ACCEPTED_CANDIDATE_FIXTURE.
- Latest 2026-10-16: BE2-01 **Q01/B6_CR01_R2_PENDING_CODEX_REVIEW** (Codex P2 on CR01 corrected with pytest-collected identities; package b6cr01r2 from Studio 90724453; runtime NOT_RUN; FEAT-044 PHASE_B_B6_CONFORMANCE_EVIDENCE_20261016.md §12.6). Earlier:
- Latest 2026-10-16: BE2-01 **Q01/B6_CR01_FIXED_PENDING_RUNTIME_REVIEW** (independent B6 closure CLOSE_WITH_NOTES; Person 2 chose to harden the durable runner for B6-CR01; package b6cr01 from Studio 90724453; runtime NOT_RUN; FEAT-044 PHASE_B_B6_CONFORMANCE_EVIDENCE_20261016.md §12). Earlier:
- Latest 2026-10-16: BE2-01 **Q01/B6_RUNTIME_PASS — PENDING_INDEPENDENT_CLOSURE_REVIEW** (b6fix01 Studio run USER_REPORTED_REMOTE PASS: 202 B2–B6 + 224 Phase A / 0 skip; durable runner exit 0, 39/39 required; B-12 HANDOFF; source 90724453; Studio stopped afterwards; FEAT-044 PHASE_B_B6_CONFORMANCE_EVIDENCE_20261016.md §11). Earlier:
- Latest 2026-10-16: BE2-01 **Q01/B6_FIX01_SELF_REVIEWED — READY_FOR_STUDIO_RUN** (Codex unavailable; user-directed author self-review PASS, not independent; b6fix01 runtime NOT_RUN; FEAT-044 PHASE_B_B6_CONFORMANCE_EVIDENCE_20261016.md §10). Earlier:
- Latest 2026-10-16: BE2-01 **Q01/B6_FIX01_CODE_COMPLETE — PENDING_CODEX_REVIEW** (B6 Studio run 1 USER_REPORTED_REMOTE FAIL: one restart test sent an Attempt object (B6-RT01); one-line test fix; package b6fix01 from the Studio B6 snapshot 3940e529; runtime NOT_RUN; FEAT-044 PHASE_B_B6_CONFORMANCE_EVIDENCE_20261016.md §9). Earlier:
- Latest 2026-10-16: BE2-01 **Q01/B6_CODE_COMPLETE — PENDING_CODEX_REVIEW** (durable conformance runner, B-01 restart tests, additive package b6 from fix03 3930046b; runtime NOT_RUN; FEAT-044 PHASE_B_B6_CONFORMANCE_EVIDENCE_20261016.md). Earlier:
- ACTIVE **Q01/B6_READY_FOR_HANDOFF**; **B5_CLOSED_REVIEW_PASS**.
  **B5-R01/B5-R02/B5-RT01 CLOSED_B5_SCOPE** after source-bound runtime and focused closure.
- USER_REPORTED_REMOTE fix03 run 2026-10-15T17:37:09Z (2026-10-16 00:37:09 Asia/Saigon): 193 B2-B5 passed / 0 failed / 0 skipped; 224 Phase A passed / 0 skipped; fixture 20 PASS / 215 checks / d17f58a3 unchanged (optional HTTP NOT_RUN 1). All suite/log/outer/Studio exits 0, RUNNER_RESULT=PASS. 43 source files verified as fix03 3930046b; local and reported Studio source match.
- Current source manifest: 3930046b5f04a67b6ff2a52dc70a4f12d5d7a89c2675e149ab654f00da2ab670; base 993a26cae78c0a4fe983033f03881838c886b176.
- Closure review: evidence/notes/PHASE_B_B5_CLOSURE_REVIEW_20261016.md; matching evidence/metrics/PHASE_B_B5_CLOSURE_REVIEW_20261016.json. Prior fix02 failure and local NOT_RUN records remain historical.
- B6 NOT_STARTED: conformance runner, crash-point matrix, Phase A scenarios on SQL, consolidated report and handoff under existing approved Phase B revision 3 B1-B6. Claude first rehydrates read-only from latest handover section AA, reports and stops; B6 implementation follows the agreed separate continuation message, without repeat approval.
- Parent BE2-01 IN_PROGRESS; exactly 14 business cards / WIP 1 / full-card DONE 0. B1-B5 closed at their recorded component scopes, not whole-product completion. OwnerFence ASSUMED_CONTRACT; real P1/P2/P4 integration/B-12, providers, live router and production adoption remain deferred. No other card, FEAT-018/Wan, install, service recreation, staging, commit, push or deploy. Original approvals/plans/ADR unchanged.

Use the same synthetic Studio sketch2life-backend-test. Raw remote full output is retained
inside FEAT-044 evidence/local/b5-closure-20261016/; no direct Codex cloud-execution claim.

## Current product-scope authority — 2026-10-10

Owner explicitly replaced the prior product scope with Product Scope v1.0 for Montessori-inspired collaborative creative learning. Canonical requirements are now Master SRS v3.0 at `features/FEAT-029-master-srs/artifacts/Sketch2Life_Master_SRS.md`, governed by FEAT-039 and ADR-0014. The target is ages 3–12, Child/Teacher/Super Admin, Android child clients, classroom/group sessions, personal/collaborative canvas, adaptive sketch, gallery, teacher-approved knowledge video, off-screen, reflection/portfolio and administration/privacy/recovery. Owner confirmed keeping FastAPI and React Native.

The older sections below are retained as dated/history records and implementation context. Conflicting product assumptions (under-9, adult-only roles, Parent portal/payment/credit, one-child session, fixed video duration/model and numeric retention) do not override v3.0. Existing source still follows several old policies and is not migrated by this documentation change. Owner additionally chose per-Sketch review for pilot, active-child selection by turn on shared tablets, and explicit Teacher retry/skip/end after exhausted video failure; generation still waits and never automatically skips. Exact age endpoint, child credentials, consent/retention, tenancy/capacity, retry parameters and other technology selections remain open in SRS B17. Security, provenance, inward dependencies and ADR-0006 planning separation continue. See `features/FEAT-039-collaborative-learning-scope/artifacts/REUSE_AND_ARCHITECTURE.md` for source maturity and proposed architecture. Exact old working-copy SRS v2.0 is preserved under FEAT-039 with its hash.

## Detailed SRS foundation amendment — 2026-10-10

The owner requested a more detailed SRS as the foundation for the entire system. Canonical Master SRS is now v3.1 under FEAT-029, governed by FEAT-039 documentation plan/approval revision 3. B19–B26 add state/policy/concurrency/recovery, 38 detailed use cases with acceptance, logical fields/API contracts, 34 screens, privacy workflows, measurement profiles and per-FR verification. Exact v2.0 and v3.0 are preserved with hashes. Current canonical v3.1 supersedes the v3.0 pointer in the earlier same-day amendment; historical records remain evidence.

Owner additionally chose a one-school pilot with expansion preparation; teacher-managed child profiles and QR/session code, without separate child login accounts; school collection of legal-representative consent with authorized Teacher/Admin recording evidence and purposes. Owner then confirmed inclusive 36–155 completed months, one simultaneous class with at most 40 children as pilot target, and default session/artwork retention 90 days after session end. Organization schema, admission/grant/turn mechanics, verification process, age calculations and device/model/performance parameters remain proposed or open as labelled in SRS B17/B19. Enrollment and role are not consent; capacity is not proven. Portfolio/profile/audit/copy policies remain separate, without silently extending raw-source retention.

Only documentation changed in this task. Existing source is not migrated; Android/FastAPI/React Native remain the confirmed technologies. Other runtime/editor/sync/DB/queue/storage/model/web/deployment choices need the applicable ADR and feature approval. ADR-0006 independent Sprint 1 workstreams and separate integration allocation continue.

## Current four-person task allocation amendment — 2026-10-10

For the replacement SRS v3.1, the owner now requests one FE, two BE and one person who connects all other parts, with ordinary task lists and no calendar/duration estimates. FEAT-040 and ADR-0015 record this explicit staffing amendment. Current planning artifact: `features/FEAT-040-four-person-delivery-plan/artifacts/TEAM_TASK_BREAKDOWN.md`, 57 proposed runtime cards with module/FR/API/data/UI ownership and versioned handoffs.

P1 owns Android and Teacher/Admin UI, P2 core/classroom/collaboration/data, P3 AI/content/media, P4 technical composition/connectors and combined validation coordination. Component owners retain their logic/adapters/tests/fixes. Four independent fixture runners continue under ADR-0006's principle; historical BA/AI/animation/media role labels do not override this newer owner split. Integration allocation is now intentionally recorded, but every runtime feature still needs its own approval. No runtime or SRS bytes are changed by this planning task; task counts are not effort estimates or proof of implementation.

## FEAT-018 legacy branch integration amendment — 2026-10-10

Owner directly requested merging the existing codex/feat-018-contract-plan into dev after the SRS/task publication. FEAT-042 records pinned history, direct approval, conflict/regression reconciliation and offline verification. The incoming branch includes FEAT-030 whiteboard/story-video and UI scaffolds; these remain legacy/experimental and do not override canonical SRSv3.1 or complete its runtime migration. Existing dev guards, Pixi flow and immutable artifacts are preserved. Thirty-four incoming target images/crops remain dormant without verified visual approval. Missing media dependencies and model/GPU/device/visual acceptance remain explicit gates; no live provider or deployment is performed.

FEAT-042 integration completed with merge429e9c6 published to dev and verified retaining both sourcef959426 and prior dev396b4f6. Available offline checks passed: backend2001, mobile22, renderer67 and exact-index web export. Protected SRS/task bytes and original pending runtime work remain unchanged. Actual receipts and environment limits are in FEAT-042 evidence/notes/PUBLICATION.md and VALIDATION.md.

## Purpose

Sketch2Life is now a Montessori-inspired collaborative creative learning platform: children draw, cooperate, receive teacher-controlled AI assistance, explore knowledge/video, perform off-screen activities and reflect; teachers coordinate classroom/group sessions and observe each child's progress.

## Current phase

`FOUNDATION_PUBLISHED`

## Environment policy (owner override, 2026-10-10)

- Windows is the code-development, repository-management and lightweight-static-test environment.
- Do not install new PyTorch, CUDA/cuDNN, Diffusers, Transformers, Accelerate,
  xFormers, model weights, large datasets, Docker images or GPU-specific packages on Windows.
- If a required local dependency is missing, record `REQUIRES_LIGHTNINGAI_TEST`;
  do not call the test passed.
- LightningAI is the dependency-installation, GPU/inference and integration-test
  environment. Use a separate Sketch2Life virtualenv and do not modify the existing
  Wan2.2 environment.
- The canonical workflow is `scripts/lightningai/setup.sh`, then read-only
  `verify.sh`, then `run_tests.sh`. Setup requires explicit
  `SKETCH2LIFE_ALLOW_INSTALL=1`; no script uploads child media or downloads model
  weights implicitly.
- `LOCAL_CODE_READY`, `LIGHTNINGAI_ENVIRONMENT_READY`, `LIGHTNINGAI_TEST_PASS` and
  `VISUAL_QA_PASS` are separate gates and must not be conflated.

The workspace harness and approved architecture skeleton are established and securely published to the project repository. Product feature code must not be started until that feature's plan and relevant task approval are recorded.

## Owner product-scope amendment — 2026-10-06

- Supported child population is younger than 9 years: 0–107 completed months inclusive, across product bands 0–3, 3–6 and 6–9.
- At 108 completed months, a child is outside the supported product target; age-sensitive session and GenAI requests are rejected before provider execution.
- Keep existing 9–12 Montessori catalog rows as source data for future scope; do not return them for current product sessions.
- Age comes from an adult-confirmed profile/session context. The system must not infer age from drawings, narration, or model output.
- Owner-approved capstone-trial package assumptions: Free 10 credits/month; Gia đình 99,000 VND/month with 30 pooled credits for up to 3 child profiles; Lớp học 499,000 VND/class/month with 120 pooled credits for one Guide and up to 25 assigned profiles. One-time top-ups: 10/49,000 VND, 30/129,000 VND, 60/239,000 VND.
- One credit covers a completed adult-approved drawing/story experience through the off-screen handoff; reserve at session start, debit after successful handoff, release on failure/cancellation, and make same-session retries idempotent. Paid monthly plans are manually renewed; backend verifies payment before entitlement/credit grant. No provider or live billing integration is selected; see FEAT-037.

## Confirmed from the user's request

- Context must be retained in detail.
- Each feature is isolated in its own folder.
- Evidence belongs inside each feature folder.
- The codebase must have a deliberate clean-architecture layout.
- Frontend visuals must be generated first, reviewed/approved, and only then applied.
- Work must have a plan and explicit approval before implementation.
- The next decision is to ask focused questions and finalize the technology stack.

## Confirmed project decisions from the project owner

- Client target: mobile-only.
- Team: four people; all can contribute across disciplines.
- AI hosting: Lightning AI is required for real-model testing.
- Backend hosting: provider-agnostic initially; AWS-compatible deployment is acceptable later.
- Test data: fixtures/synthetic data only; no real child data in the MVP development loop.
- MVP ambition: cover the full experience, divided into four owned workstreams.
- Delivery model: Sprint 1 uses four independently runnable, fixture/contract-driven workstreams; integration runtime work is deferred to a separately planned Integration Sprint.
- Planning distinction: the project roadmap is dependency-driven, while team sprint assignment is parallel-workstream-driven; one must not be used as the other.
- Mobile delivery: Android-only, bare React Native, one app with adult Parent/Guide modes and supervised child participation; child has no role or credential.
- Android identity and support: `com.sketch2life.mobile`; minSdk 29, targetSdk 36, compileSdk 37.
- AI connectivity: every provider is backend-only through an authenticated adapter; the current Lightning account is not treated as private networking.
- AI provider lifecycle: Lightning AI is fixture/dev only on the current normal account; Runpod Serverless is the production target behind the same backend port.
- Async progress default: bounded HTTP polling for MVP, revisited only with measured evidence.
- Authentication: Firebase Authentication only, verified by the backend; test uses the owner-controlled real Firebase project; no Firebase Storage/Firestore/Realtime Database.
- Account model: parent/guide users authenticate with Google Sign-In or email/password; child mode has no independent child account.
- Ownership model: each ChildProfile has exactly one Owner Caregiver (parent or legal guardian); one Owner Caregiver can create many ChildProfiles; ChildProfile has no login credential.
- Guide model: a ChildProfile can have multiple Guide assignments, including overlapping assignments. Parent-created assignments are effective immediately and notify the Guide; exceptional Admin-created assignments notify both Owner and Guide. Share durations are 3/7/15/30 days, and the Owner can revoke immediately.
- Session model: each Guide can run one session at a time. A Guide session notifies the Owner, exposes a live redacted projection to the Owner, and stops immediately when the Owner revokes the Guide assignment.
- Product surfaces: mobile, desktop Guide Console and responsive Parent Web are all target operational surfaces using the same backend authorization. Parent Web is not implicitly a session runner unless a separate command contract is approved.
- MVP media scope: personalized animation, narrated story, and learning micro-video are included in the owner-approved MVP target. Research dataset release remains separately gated.
- Observability: durable domain/session events and audit records are authoritative. Grafana is an operations/dashboard layer over redacted logs, metrics, and traces; raw child media and credentials never enter telemetry.
- Child data lifecycle: Owner selects 30/60/90 days for child/session data classes. Expired data becomes inaccessible archive data before purge. Audit retention follows a separate policy. Admin raw-content access is break-glass, reason-required, temporary in scope, and audited.
- Ownership: the project owner controls Firebase/Google Play accounts and Android release/upload key custody.
- Artifact storage: S3-compatible storage owned by backend ports; no direct mobile bucket access.
- Android delivery: installable APKs for internal testing first, then signed AAB through Google Play test tracks to public release.

## Reference baseline, not yet a final decision

The attached handbook proposes a modular monolith plus workers, a FastAPI/Pydantic backend, PostgreSQL, S3-compatible object storage, Redis/RQ, PixiJS + GSAP for deterministic original-art animation, and a separate AI plane. Based on the owner's answers, the current proposal is React Native + TypeScript for the mobile app, with a PixiJS + GSAP renderer embedded behind a controlled mobile bridge, and the handbook's Python AI/backend baseline. Exact model profiles and cloud services remain benchmark/approval decisions.

## Product invariants carried into the harness

- Original child media is immutable and every derivative has provenance.
- Human Gate A confirms/corrects multimodal understanding.
- Human Gate B approves both activity identity/version and learning-objective identity/version.
- Deterministic safety, age/readiness, prerequisite, and material rules run before any model selector.
- Personalized art animation operates on the child's original artwork; generated learning media is a separate artifact.
- Reviewed learning assets are resolved before cache-miss generation.
- Media failure falls back to simpler safe content and does not remove the off-screen activity.
- A session reaching a ready state must end in an off-screen activity handoff and feedback path.
- Sensitive child data has consent, least-privilege access, retention, and deletion semantics.
- OwnerCaregiverOwnership is the only ownership relationship for a ChildProfile; GuideAssignment grants time-bounded delegated access and never transfers ownership.
- Guide revoke invalidates new access immediately and stops an active Guide session with an in-product message and audit/notification events.
- Parent live monitoring exposes the necessary session projection while applying data minimization to technical metadata.
- Business event history and security audit history are separate from Grafana technical telemetry.

## Open decisions

See `features/FEAT-001-stack-and-team-plan/TEAM_ALLOCATION.md` and ADR-0006 for the revised Sprint 1 allocation, FEAT-008 for the generic skeleton, FEAT-009 for Android foundation, and FEAT-010 for auth/release/AI-provider strategy. Remaining integration questions are listed in `docs/setup/SYSTEM_QUESTIONS.md`.

The following remain open and must not be invented by implementation: exact notification channel/retry matrix; Guide field-level access to raw media/history; Parent Web session-creation command UX; break-glass dual approval, notice and time window; physical deployment details; legal-guardian verification and child assent for age 7+; backup/provider-copy deletion; production SLO/RPO/RTO; account lifecycle and Admin provisioning. Test-stage rate limits, redacted backend monitoring and adult-only role enforcement are requirements, not optional scope.

## Local Android development connectivity baseline — 2026-09-28

`apps/ui-mobile` uses Expo SDK 52 with a native development client. The supported local launch
paths are LAN mode for physical devices and explicit ADB reverse mode for localhost/emulator use.
The repository records this recovery in FEAT-032; a host Metro probe alone does not prove that an
Android device can reach the server, and device reload evidence requires a connected ADB device.

## Master SRS scope closure — 2026-09-19

The owner-approved target baseline is recorded in `features/FEAT-029-master-srs/artifacts/Sketch2Life_Master_SRS.md` v1.8 and the feature evidence notes `OWNER_SCOPE_CLOSURE_20260919.md`, `OWNER_REQUIREMENTS_CLOSURE_20260923.md` and `SRS_DETAIL_EXPANSION_20260923.md`. It covers the B4–B12 workflow plus complete SRS sections for actors, relationships, schemas, contracts, state, security, observability, retention, Parent Web, verification and implementation-grade test detail. On 2026-10-06 the owner superseded the earlier 0–12 product age target with `<9` / 0–107 completed months; FEAT-029 v1.9 records that amendment. This is a requirements baseline; it does not authorize unrelated provider calls, cloud provisioning, contract migration or deployment.

## Cross-workstream review snapshot — 2026-09-05

Remote workstreams P1 b3f397c, P2 f3014e5, P3 68aceeb and P4 f0dd622 have independent implementations. They are not an integrated runtime and are not merged into the foundation main baseline. FEAT-015 records pinned branch readiness, reproduced test evidence and proposed integration/test gates. ADR-0006 remains unchanged; integration allocation/implementation still requires separate approval. P4 branch context/plan status is stale relative to its approval/code and is explicitly flagged in the review rather than silently corrected here.

## Session-only Montessori profile and mask-quality increment — 2026-09-29

The owner-approved integrated FEAT-018/020/030 increment adds request-scoped explicit child learning
context to deterministic activity ranking, plus offline SAM2.1 candidate checks and pigment-safe
mask-bounded cutout reconstruction. ADR-0010 fixes the current boundary: profile edits remain
volatile/session-only, with no new durable backend record or storage-provider decision. Backend,
mobile, renderer and security evidence is indexed under the owning FEAT-018/020/030 records. Real
SAM/L4 performance, held-out mask quality and Android emulator visual acceptance remain open; a
synthetic selector score is not a real-model quality claim.
