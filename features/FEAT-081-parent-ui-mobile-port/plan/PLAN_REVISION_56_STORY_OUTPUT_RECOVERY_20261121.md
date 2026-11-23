# Plan Revision 56 — Parent story output recovery and truthful loading state

**Date:** 2026-11-21  
**Status:** APPROVED  
**Canonical requirements:** FEAT-063 SRS v2.7-draft, §§1–31. This plan does not change the product SRS or the three-rewrite maximum in BR-13.

## 1. Goal

Repair the real Parent failure observed on Android: Qwen3.5 returned syntactically complete JSON whose story prose failed the existing completion gate. Make the loading and terminal states accurately reflect server status, then resume the same synthetic run through adult story review and, only if all normal gates permit, one silent video candidate.

## 2. Evidence and cause

- Synthetic StoryRun: `b05c2b46-e760-4643-824b-b30b5387453f`; synthetic turtle artwork and 60-month synthetic profile.
- One story call `fc-01M7Y9SCQQP9RCJXARXQBDX25G` completed in 77.185 seconds inference / 102.295 seconds worker time. API returned `502 STORY_OUTPUT_INVALID`; worker error was `STORY_TEXT_INCOMPLETE` at `story.opening`.
- JSON parsed completely and generation used 682/4096 tokens. The opening and middle approached their character caps but lacked complete sentence endings; scene actions and narration also failed the existing sentence gate. This is a content-contract/prompt failure, not timeout or container availability.
- `82-story-inference-started.png` shows a high-contrast purple loading card, spinner and elapsed timer, but only generic “Đang xử lý” status. `83-story-failure.png` displays a misleading “Gửi lại cùng yêu cầu” action even though worker-output invalidation is not retryable through that retained request.
- Addendum 102's one-story-call cap and stop-on-failure condition were reached. No follow-up code or inference is authorized by that addendum.

## 3. Proposed implementation

### M0 — Inspect the existing run and exact contracts (read-only)

Confirm the failed revision, retry state, selected activity receipt, and current StoryRun version through authenticated read-only status. Confirm the run still permits a new adult-directed rewrite under the current API. Do not mutate the run during M0. If the state or receipt is ambiguous, stop and report it.

### M1 — Make story generation completion-aware without weakening quality

- Change the worker's internal structured response for story prose fields to a bounded `{body, terminator}` object; `terminator` is constrained to `.`, `?`, or `!`.
- Apply it to opening, middle, ending, each scene action and narration. Validate the body for Vietnamese script, non-empty meaning, and dangling conjunctions before composing the sentence.
- Keep the current final complete-sentence validator as a hard gate. Never append punctuation to an incomplete body to make it pass.
- Set shorter, model-appropriate body targets/caps and align the worker JSON schema, parser, backend public schema and prompt. Keep exactly five scenes, confirmed subject, selected activity, drawing provenance, age personalization, Vietnamese language, safety and adult-review requirements.
- Add safe failure diagnostics limited to field path, character count, configured cap and validation result. Do not log prompt, raw output, image or child data.

### M2 — Correct Parent loading and failure actions

- Preserve the prominent animated loading card and elapsed timer. Show only server states actually known (`đang gửi`, `đang xử lý`, `đang đối soát`); do not invent percentages or worker-stage progress that the API does not report.
- Replace the generic terminal retry button with an explicit adult-directed “Gửi gợi ý để viết lại” action, shown only when the API confirms the run is stable and the previous revision is `FAILED`. Require an adult instruction and create a new idempotent revision; do not replay the failed idempotency key.
- Keep stale/failed drafts unconfirmable. Enforce the existing BR-13 maximum of three adult-directed rewrites; no direct scene editing and no automatic retry.
- Make terminal invalid-output copy say that the draft was rejected and is not available for confirmation. Provide a safe exit to lesson/history while preserving the run and its data.

### M3 — Focused verification, then one real UI request

- Add worker contract tests for complete/incomplete bodies, each permitted terminator, Vietnamese-only text, dangling clauses, overlength and exact JSON shape; add backend contract tests for unchanged public story shape and retry/idempotency rules; add mobile tests for loading and terminal actions.
- Run focused tests, mobile typecheck/tests, security validator, `git diff --check`, rebuild only the task API, deploy only the language/audio Modal app and verify health before the request.
- If M0 confirms the existing run accepts a new adult-directed revision, send exactly one new story request from the real Android UI with an explicit short instruction derived from the rejected field-level quality error. If it does not, stop; do not create another run or call drawing/activity AI under this amendment.
- If that story passes all hard gates, show it to the adult and require confirmation. Then allow at most one silent video candidate through the real UI using the existing video worker, only if existing consent, admission, safety and ownership checks pass. No quota/payment API access or bypass. Stop at the first error.
- Capture screenshots, API status, Modal call ID and timings. Never store raw model output, prompt, token, credentials or child data.

## 4. Scope and limits

- This amendment authorizes no account/profile creation/deletion, seed changes, database migration, quota/payment call or bypass, quality/safety/consent relaxation, fixture, preview harness, direct worker inference, or direct API inference.
- One new story inference only, and one video candidate only after a valid adult-confirmed story. Drawing/activity calls are not repeated.
- Use the current synthetic Parent and existing run/artwork only. If the current run cannot accept a new revision safely, stop instead of creating a run.
- Stop the task-used Modal apps after confirming no live tasks. Leave unrelated Modal apps and Docker projects untouched.
- No commit or push.

## 5. Acceptance criteria

1. A semantically incomplete story sentence remains rejected; a complete, concise Vietnamese story passes without the model saturating field limits.
2. Public API response shape and all SRS hard gates remain intact.
3. The real Parent UI never shows a replay action for a non-retryable retained request; an explicit adult rewrite uses a fresh idempotency identity and the existing three-rewrite cap.
4. Loading remains visually prominent and accurately reports server-known state without fabricated percentage or stages.
5. One real UI story request reaches adult review, and optionally one video candidate reaches its actual terminal UI state; otherwise the first exact blocker is reported. No quota/payment call or bypass.

## 6. Allowed files

- `deployment/modal/srs_v23/language_audio_app.py`
- `deployment/modal/srs_v23/tests/test_parent_story_output_contract.py`
- `backend/tests/unit/test_ai_story_contracts.py`
- `apps/ui-mobile/src/parent/presentation/components/ParentAiLoadingState.tsx`
- `apps/ui-mobile/src/parent/presentation/screens/StoryScreen.tsx`
- `apps/ui-mobile/src/parent/presentation/navigation/parentFlowV1.ts`
- `apps/ui-mobile/src/parent/presentation/navigation/useParentController.ts`
- `apps/ui-mobile/src/parent/presentation/ParentExpoApp.tsx`
- `apps/ui-mobile/tests/parentFlowV1.test.ts`
- `apps/ui-mobile/tests/parentSrsBehavior.test.ts`
- This plan, `approvals/TASK_APPROVAL.md`, `CONTEXT.md`, `status/STATUS.md`, and `evidence/PARENT_LOADING_E2E_REV53_20261121/`
