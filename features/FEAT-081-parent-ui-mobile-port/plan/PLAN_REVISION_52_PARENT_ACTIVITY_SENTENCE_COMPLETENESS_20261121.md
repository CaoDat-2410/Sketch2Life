# Revision 52 — Parent activity sentence completeness

**Status:** APPROVED by the owner's direct instruction to inspect and fix backend defects as well as mobile behavior.  
**Date:** 2026-11-21  
**Worktree:** `feature/fe-mobile-remediation`

## Observed backend defect

The real Parent UI flow completed drawing recognition and requested activity suggestions through the mounted backend route. The catalog adapter reported zero accessible lessons and zero eligible candidates, so the approved no-match path asked Qwen for three fallback activities. The route logged `parent_activity_suggestions_completed` with `selection_mode=AI_GENERATED_FALLBACK` and `activity_count=3`.

The persisted response contains sentence fields ending in clipped phrases, including `... con r.`, `... môi trường tự.`, `... khu vườn để trẻ.`, `... hình lục.`, and `... hoặc có.`. The worker parser composes a period onto generated sentence bodies. The backend quality gate checks terminal punctuation and basic length/content markers, so those incomplete phrases pass and are persisted as a completed suggestion set. The actual UI displays them to the adult reviewer.

This is a backend and Modal worker contract defect. It is not a frontend-only rendering issue; the database snapshot has the same incomplete strings.

## Scope

1. Add conservative Vietnamese sentence-tail completeness checks for AI-generated fallback text in the Modal worker parser. Reject consonant-only fragments, configured dangling Vietnamese function-word endings, and the observed incomplete compound patterns before producing a successful worker contract.
2. Add a matching backend application quality gate for AI-generated fallback activities so malformed output cannot be persisted even if a worker version fails to reject it. Preserve catalog-selected teacher-authored activity behavior.
3. Keep public API field names, response schema, catalog-first behavior, fallback count, adult review, safety checks, and activity-selection semantics unchanged. Do not relax existing quality or safety gates.
4. Add focused offline unit/contract tests for each observed incomplete tail and valid nearby complete Vietnamese sentences. Run only the focused test files.
5. Preserve the current run and its saved response as evidence. Do not select the malformed activities, mutate or delete the saved snapshot, or continue to story from this invalid set.

## Explicit limits

- The current activity Modal call has completed. Do not retry it, regenerate it, or make another activity inference on this run.
- No Modal deploy, warm-up, stop, or additional request. This change is code/test-only; live worker verification requires a separately approved fresh run.
- No direct API/worker bypass, business database edits, migration, reset/reseed, new account/profile/run, quota/payment, fabricated consent, real child data, gate relaxation, `.env`/secret/SRS change, unrelated service shutdown, commit, or push.
- Existing Addenda 80–87 remain in force.

## Acceptance criteria

- The exact observed truncated sentence examples fail closed in both worker parsing and backend fallback quality validation with stable non-content diagnostic codes.
- Complete Vietnamese sentence examples and valid catalog selection continue to pass.
- Focused worker and backend tests pass; repository security validation passes.
- No second Modal inference occurs. The current run remains unmodified at the activity-review screen, and the evidence report records that story generation stopped because the accepted activity result is malformed.

## Files permitted to change

- `deployment/modal/srs_v23/language_audio_app.py`
- `deployment/modal/srs_v23/tests/test_qwen35_lesson_suggestion_contract.py`
- `backend/src/sketch2life/application/services/parent_activity_suggestions.py`
- `backend/tests/unit/test_parent_activity_suggestions.py`
- `features/FEAT-081-parent-ui-mobile-port/approvals/TASK_APPROVAL.md`
- `features/FEAT-081-parent-ui-mobile-port/plan/PLAN_REVISION_52_PARENT_ACTIVITY_SENTENCE_COMPLETENESS_20261121.md`
- `features/FEAT-081-parent-ui-mobile-port/CONTEXT.md`
- `features/FEAT-081-parent-ui-mobile-port/STATUS.md`
- `features/FEAT-081-parent-ui-mobile-port/evidence/PARENT_BACKEND_FRONTEND_FIX_E2E_20261121/`
