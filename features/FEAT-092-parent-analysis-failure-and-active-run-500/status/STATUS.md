# FEAT-092 status

**State:** Implemented locally; not committed, not pushed.

| Item | Result |
|---|---|
| A. `ParentActivityV1` provenance fields | Added 8 optional fields; `tests/unit/test_parent_main_activity_snapshot_schema.py` passes. |
| B. Worker builtin exception classified terminal | `_is_remote_user_code_failure` in `modal_function_client.py`; 2 new tests in `test_story_run_lite_photo_bridge.py` pass, plus `test_modal_story_function_client.py`. |
| C. App stops spinning on `AWAITING_RECONCILIATION` | `useParentController.ts settleDrawingStage`; `parentPhaseBWiring`/`parentDrawingTerminal` vitest pass. |
| API container rebuilt | `sketch2life-api-1` healthy; no ValidationError after restart. |

Not verified: end-to-end on a device; the Modal `AttributeError` root cause (needs `modal app logs` from the deploy workspace).
Pre-existing, unrelated failures seen: `tools/validate_repository_security.py` (FEAT-085 path, dev-seed script), `tsc` errors in `VideoScreen.tsx`/`ParentVisualPreviewHarness.tsx`, broad contract-test failures in the ad-hoc test container.

## Rev 2 device result (2026-11-25)
- Emulator `emulator-5554`, generated crayon-style chicken drawing, topic Động vật / Thỏ con.
- `drawing.analyze` completed in 223 s (cold start); app showed "con gà con", 100%, features lông vàng nhạt, mào và mồng màu đỏ, mỏ màu cam, bụng bầu dục xanh dương.
- Not committed. Not verified: later steps (subject confirm, story, video), warm-container latency, other drawings.

## Rev 3 device result (2026-11-25)
- Activity step: `parent.activity.suggest` completed in 446 s; 3 Vietnamese activities shown, selection saved, context confirmed.
- Story step: failed with `STORY_INPUT_CONTRACT_INVALID` (v1 vs v3 input) before any Modal call; fixed in the repository, API rebuilt.
- NOT verified: story generation after the fix, story review, video. The app returned to the sign-in screen after a cold restart.
- Leftover merge reject file: `backend/src/sketch2life/infrastructure/persistence/parent_story_repository.py.rej`
  (FEAT-087 subject-role hunks never applied); `backend/tests/unit/test_parent_activity_worker_contract.py` cannot import
  `_story_primary_activity` against `HEAD` (now defined again).

## Rev 4 end-to-end device result (2026-11-25)
Emulator, crayon-style chicken drawing, run 92739813-...:
| Step | Result |
|---|---|
| Drawing analysis | OK, 187-218 s, "con gà con" 100% |
| Activity suggestions | OK, 282-446 s, 3 activities |
| Story generation | OK, 287 s, "Gà con tìm dấu chân", 5 scenes, adult confirmed |
| Video | NOT working: `POST /v1/story-runs/{id}/video-generations` -> 503 PROVIDER_UNAVAILABLE |

Video cause: `app.state.story_video_ports` is `None` unless `Settings.story_video_adapters == "local_test"`
(fixture adapters). No Modal video adapter is composed on this route. The separate dev router
`parent_video_candidates.py` (Modal silent video) reads `Settings.parent_video_dev_candidate_enabled`, a field that does not
exist in `Settings`, and is not mounted by `create_app`. Both belong to the video feature, not to this fix.
