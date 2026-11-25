# FEAT-092 plan (Rev 1)

## Scope
- A. Declare the 8 optional provenance fields on `ParentActivityV1`; refresh OpenAPI golden.
- B. Modal drawing wait: a remote exception that is not a timeout and not a dispatch/transport failure
  after the call was accepted and the function ran to completion is a terminal worker failure
  (recoverable, retake allowed), not outcome-unknown. Timeouts stay outcome-unknown.
- C. App: `AWAITING_RECONCILIATION` must not spin silently for the whole budget; show an explicit
  "kết quả chưa rõ" message with a close-run action after a short grace period.

## Out of scope
Root-causing the Modal `AttributeError` itself (needs Modal logs from the deploy workspace); SVG guide redesign.

## Acceptance criteria
1. `ParentMainActivityV1.model_validate` accepts a suggestion-based snapshot containing the 8 fields.
2. A worker `AttributeError` from `call.get` yields `ModalFunctionExecutionFailed`, so the run ends
   `INPUT_REVIEW` + `job_state FAILED` with a retryable error; `TimeoutError` still yields outcome-unknown.
3. App surfaces a message (not endless spinner) for `AWAITING_RECONCILIATION`.
4. Unit/contract tests for 1-3 pass; `tools/validate_repository_security.py` passes.

## Amendment Rev 2 (2026-11-25, owner asked to fix everything found and test on device)
- D. Modal `qwen-worker` routes used non-existent `Function.get_raw_f()`; replaced by `Function.local`.
- E. Drawing model returned 3-number boxes (bottom edge missing) so every analysis failed `BOX_SHAPE_INVALID`;
  box schema is now an object `{left,top,right,bottom}` normalized to `[l,t,r,b]` in the worker.
- F. Content-free diagnostics: `box_shapes`, `masked_structure` (strings masked).
- G. Fixed tsc errors (`VideoScreen.tsx`, `ParentVisualPreviewHarness.tsx`).
Deploy: `modal deploy --profile hieuptse184252 --env dev deployment/modal/srs_v23/language_audio_app.py`.

## Amendment Rev 3 (2026-11-25, owner asked to run the remaining flows)
- H. Activity suggestions: worker drafts 4 activities, drops any that fail a text-quality gate (words are never
  repaired) and keeps at most 3; backend `ParentActivitySuggestionWorkerResponseV2` accepts 1-3 drafts on NO_MATCH.
  Owner decision in chat: "gen nhiều hoạt động, cái nào pass quality gate thì hiển thị, tối đa 3".
- I. Story input: `reserve_story_revision` built `story-generation-input.v1` while the Modal client/worker validate
  `v3`; it now builds v3 (topic, lesson pin notes, `primary_activity` + hash) and requires an activity selection.
  `HEAD` already had this mismatch (the v3 code from 77635688 was lost in a merge).

## Amendment Rev 4 (2026-11-25, owner: "chạy được trên UI từ đầu tới cuối thì ok")
- J. Three code paths built the Parent story worker input: `parent_story_repository.reserve_story_revision` (v1),
  `story_run_lite/repository.reserve_story_revision` (v1) and `persistence/story_first_start.FirstStoryStarter`
  (v2, the path the app actually uses after context confirmation). All now build v3 for a Parent run
  (Teacher keeps v2). Tests updated: `test_story_first_start.py`, `test_parent_activity_selection_postgres.py`.
- Out of scope, reported: the video step (see STATUS).
