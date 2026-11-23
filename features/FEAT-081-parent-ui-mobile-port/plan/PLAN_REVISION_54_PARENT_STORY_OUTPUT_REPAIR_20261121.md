# Plan Revision 54 — Parent story output repair and bounded UI continuation

**Date:** 2026-11-21  
**Status:** Approved by the owner's active request to continue fixing the real Parent workflow, make loading states visible, and run end to end without quota/payment management.  
**Canonical requirements:** FEAT-063 SRS v2.7-draft, §§1–31; local Rev58–Rev67 amendments as recorded by `docs/context/SRS_AUTHORITY.md`.

## 1. Goal

Repair a malformed Parent story draft already shown on the real Android UI, then make one bounded, adult-directed rewrite through the existing UI. The first story call completed in Modal but returned mixed CJK characters and unfinished Vietnamese prose; the backend accepted and persisted it. Prevent malformed output from being accepted at both worker and API contract boundaries. Strengthen the prompt so the child's confirmed drawing remains the story anchor and the selected outdoor activity is framed as a future activity after the video, not as already performed. If the single rewrite passes, continue adult review and at most one silent video candidate through the Parent UI, without calling quota/payment APIs.

## 2. Existing run and evidence

- Reuse only StoryRun `08657e31-ebd7-4a07-8f9b-5929b4dff23b`, its existing synthetic Parent/profile, confirmed turtle drawing, confirmed subject, selected activity, and the already persisted first draft.
- The first story Modal call succeeded with call ID `fc-01M7XYHYN8J2S8RAW7WNEQ2D8C`; the Parent UI showed a CJK character in Vietnamese prose and unfinished paragraph endings. Do not confirm this revision.
- The accepted activity is the UI-selected “So sánh thẻ rùa”; do not generate or change activity suggestions.
- The real Android app is `emulator-5554`; continue only through ADB/UI for product actions.

## 3. Implementation scope

1. Add strict story prose validation at the Modal worker and backend `StoryRevisionDraftV1` boundary:
   - reject CJK/non-Latin script contamination in user-facing Vietnamese prose;
   - reject incomplete story paragraphs and scene action/narration fields that lack sentence-ending punctuation or end in an obvious dangling Vietnamese connector;
   - return a stable safe diagnostic code and field category only; never log or return raw generated text in diagnostics;
   - retain existing schema, age, topic, consent, safety, butterfly-fact, and scene-count rules.
2. Strengthen the Vietnamese story prompt:
   - the confirmed subject as depicted by the selected child drawing remains the central subject;
   - do not invent visual features beyond confirmed visible features;
   - the chosen activity is scheduled after video and may shape a future invitation/knowledge cue, but must not be narrated as already completed;
   - all user-facing prose must be complete, natural Vietnamese; no other writing system; exactly five scenes.
3. Add focused offline tests for the observed Chinese contamination, incomplete paragraphs, dangling endings, and a valid Vietnamese story. Add a prompt regression test.
4. Deploy only the existing language-audio Modal app and rebuild only the task API container. Do not migrate, reseed, recreate database/volume, or change `.env`/secrets.

## 4. Bounded live continuation

- After code, focused tests, and health checks pass, use the real Parent UI to submit **one** rewrite of the current draft with a short adult instruction: center the story on the turtle drawing, keep “So sánh thẻ rùa” as a future post-video activity, use complete natural Vietnamese, and preserve the confirmed visible features.
- No automatic retries. Stop on timeout, uncertain dispatch, any new failure code, or another malformed draft. Do not call story creation directly, a worker directly, or any endpoint outside the UI.
- If the rewritten story passes Vietnamese completeness, drawing grounding, age fit, selected-activity consistency, and existing safety review, inspect and confirm that exact revision in the UI.
- Only after confirmation, submit at most one silent video candidate from the real Parent UI under all existing synthetic-dev identity/admission/safety guards. Do not relax any guard.
- Do not access, read, mutate, or purchase quota/payment. If the existing synthetic candidate configuration cannot admit the candidate without quota bypass, stop and record that blocker.

## 5. Allowed files

- `deployment/modal/srs_v23/language_audio_app.py`
- `deployment/modal/srs_v23/tests/test_parent_story_output_contract.py`
- `backend/src/sketch2life/contracts/schemas/ai_story.py`
- Focused backend story-contract/API tests only if required for the new validator
- This plan, `approvals/TASK_APPROVAL.md`, `CONTEXT.md`, `status/STATUS.md`, and `evidence/PARENT_LOADING_E2E_REV53_20261121/`

Do not modify Parent account/profile/auth, consent, database migrations, activity inference, video worker, SRS, quota/payment, other Modal applications, or unrelated UI behavior.

## 6. Acceptance criteria

1. Offline tests reject the observed mixed-script and incomplete prose without exposing generated text; valid Vietnamese story output remains accepted.
2. Backend refuses malformed story output before persistence; the UI does not confirm an invalid revision.
3. The single UI-driven rewrite either yields a complete, coherent Vietnamese draft for the confirmed turtle drawing and selected future activity, or terminates with an explicit safe failure. No second rewrite or story-generation attempt.
4. If and only if the draft passes adult review and all existing gates, one silent video candidate reaches its actual UI result state. No quota/payment endpoint is called.
5. Evidence records UI screenshots, request/call IDs, elapsed times, safe status/error codes, and final state; it omits credentials, image bytes, and raw worker prompts/log text.
6. No commit or push.
