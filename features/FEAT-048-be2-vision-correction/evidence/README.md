# Evidence index

- Current C2 state (2026-10-17 11:59 +07:00): CODE_REVIEW_PASS_WITH_NOTES in
  notes/C2_CODEX_REVIEW_20261017.md and metrics/C2_CODEX_REVIEW_20261017.json (root652 passed/5
  pre-existing skips, additional adapter9/9, no actionable finding); owner ACCEPTED the offline
  component, verbatim ../approvals/C2_COMPONENT_ACCEPTANCE.md. Commit plan, executed locally as four commits (not pushed):
  notes/C2_PUBLICATION_PLAN_20261017.md. Full card IN_PROGRESS/NOT_DONE.

- History (planning stage, superseded by the approval/acceptance above):
  notes/C2_PLAN_REVIEW_20261017.md and metrics/C2_PLANNING_CHECKS_20261017.json: C2 revision2
  source/code planning review and actual document checks; DRAFT / NOT_APPROVED at that time.
- ../plan/C2_TYPED_CONTEXT_PLAN.md: C2.1–C2.5 / C2-A01–A14 and Q1–Q5 (approved since; see above).
  Claude prompt and approval template stay ignored under local/claude/prompts/; templates grant no authority.

- notes/SOURCE_AUDIT.md: SRS/card mapping, legacy reuse and gaps; planning evidence only.
- notes/PLAN_REVIEW.md: independent plan/prompt review when complete.
- metrics/PLANNING_CHECKS.json: actual validators, plan hash and approval state.
- local/claude/: ignored operator prompts/approval templates, never approval by themselves.
- notes/C1_IMPLEMENTATION_EVIDENCE.md: C1 commands/results, V01–V17 mapping, findings, NOT_RUN.
- notes/H_AI_REVIEW_HANDOFF.md: consumer semantics and the missing full-card gates.
- metrics/C1_COMPONENT_CHECKS_20261016.json: final C1 checks, JUnit/source/example hashes.
- ../fixtures/h_ai_review/: deterministic synthetic consumer examples (pinned by a test).
- local/junit/: ignored JUnit XML of the final runs (hashes recorded in the metrics file).

Implementation evidence must map V01–V17 to actual commands/tests/results and record source,
environment, UTC time and synthetic input hashes. Keep repeated raw logs/scratch local; preserve
FAIL/before and PASS/after. Fake/component, real provider/runtime and integrated proof stay
distinct. Missing required dependency/test = NOT_RUN, not PASS. No real child data or secrets.

## Independent C1 code review —2026-10-16

- notes/C1_CODEX_REVIEW_20261016.md: NEEDS_REVISION, 2 P1/4 P2; findings C1-R01–R06 open.
- metrics/C1_CODEX_REVIEW_20261016.json: reviewer source/probe hashes and actual checks.
- local/codex-review-20261016/: ignored repro scripts, before-fix failures and fact logs.
- local/claude/prompts/CLAUDE_C1_REVIEW_FIX_PROMPT_20261016.md: ignored operator prompt.

The implementation report above is historical; the independent review is the
current C1 disposition. Approval stays valid for C1 fixes, without expanding scope.

## Review fixes —2026-10-16

- notes/C1_REVIEW_FIX_EVIDENCE_20261016.md: R01–R06 → change/tests/before-after; FIXED_PENDING_CODEX_REVIEW.
- metrics/C1_REVIEW_FIX_CHECKS_20261016.json: final checks, JUnit/source/example hashes.
- local/claude-fix-20261016/: ignored before/after JUnit, logs and Codex-probe reruns.

## Codex C1 re-review —2026-10-16

- notes/C1_CODEX_REREVIEW_20261016.md: current NEEDS_REVISION, only R04 open (P2);
  other five findings closed for C1 component scope.
- metrics/C1_CODEX_REREVIEW_20261016.json: independently verified source/check receipts.
- local/codex-rereview-20261016/: ignored root and delegated probes/logs/JUnit.
- local/claude/prompts/CLAUDE_C1_R04_FOLLOWUP_PROMPT_20261016.md: ignored narrow fix prompt.

Prior implementation/review/fix reports remain unmodified historical evidence.

## R04 follow-up —2026-10-16

- notes/C1_R04_FOLLOWUP_EVIDENCE_20261016.md: reference guard fix, before/after, checks; FIXED_PENDING_CODEX_REVIEW.
- metrics/C1_R04_FOLLOWUP_CHECKS_20261016.json: final checks, JUnit and source hashes.
- local/claude-r04-followup-20261016/: ignored before/after JUnit/logs and Codex R04 probe reruns.

## Latest R04 code-review closure —2026-10-16

- notes/C1_CODEX_R04_CLOSURE_20261016.md: CODE_REVIEW_PASS_WITH_NOTES; all six
  findings closed for component scope, missing checks/owner acceptance remain open.
- metrics/C1_CODEX_R04_CLOSURE_20261016.json: source/receipt hashes and actual checks.
- local/codex-r04-final-20261016/: ignored root JUnit/logs and independent assertions.

Earlier implementation/review/fix artifacts remain unchanged historical evidence.

## Remaining-check inventory —2026-10-16

- notes/C1_REMAINING_CHECKS_20261016.md:7 server tests passed with existing Pillow;
  production route walk still NOT_RUN (python-multipart absent), no installs.
- metrics/C1_REMAINING_CHECKS_20261016.json: actual result/JUnit/source/check hashes.
- local/c1-existing-pillow-20261016/: ignored runner, both attempt logs and raw receipts.

## Complete named C1 verification —2026-10-16

- notes/C1_FINAL_VERIFICATION_20261016.md: focused233 + server7 + separate route1
  passed,0 skips, isolated dependency provenance and setup failures preserved.
- metrics/C1_FINAL_VERIFICATION_20261016.json: actual JUnit/package/source/check hashes.
- local/c1-complete-checks-20261016/: ignored dependencies, scripts, raw logs/JUnit.

Earlier missing-check reports remain historical; C1 is ready for owner acceptance.

## C1 owner acceptance and publication plan —2026-10-16

- ../approvals/C1_COMPONENT_ACCEPTANCE.md: verbatim owner acceptance of C1 (component scope only).
- notes/C1_PUBLICATION_PLAN_20261016.md: proposed GitHub file set, local-only set and commit split.

## C2 approval and implementation —2026-10-17

- ../approvals/C2_TASK_APPROVAL.md: verbatim owner approval (plan rev2, Q1–Q5); approved bytes
  ../plan/C2_TYPED_CONTEXT_PLAN_REV2_APPROVED.md.
- notes/C2_IMPLEMENTATION_EVIDENCE_20261017.md: changes, actual checks, C2-A01–A14 mapping,
  seam-test changes, review points; C2_CODE_COMPLETE_PENDING_CODEX_REVIEW.
- metrics/C2_IMPLEMENTATION_CHECKS_20261017.json: results, JUnit/source/fixture/approval hashes.
- ../fixtures/h_ai_review/typed_context_example.json: deterministic typed example (pinned by a test).
- local/c2-typed-context-20261017/: ignored C2 wrapper, raw logs/JUnit, attempt-1 receipts.

The C2 planning entries above are history (plan now approved).

## C2 Codex review, owner acceptance and commit plan —2026-10-17

- notes/C2_CODEX_REVIEW_20261017.md + metrics/C2_CODEX_REVIEW_20261017.json: CODE_REVIEW_PASS_WITH_NOTES.
- local/codex-c2-review-20261017/: ignored Codex root/delegated receipts and probes.
- ../approvals/C2_COMPONENT_ACCEPTANCE.md: verbatim owner acceptance (component scope only).
- notes/C2_PUBLICATION_PLAN_20261017.md: uncommitted-change inventory and proposed commit split.

## C2 local publication —2026-10-17

- notes/C2_PUBLICATION_PLAN_20261017.md: the executed plan (unchanged after its re-review).
- local/c2-publication-exec-20261017/: ignored executor, pinned-hash list, per-commit receipts.
