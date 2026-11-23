# FEAT-081 Rev41 — M1 implementation and video blockers

**Date:** 2026-11-20 (Asia/Saigon)  
**Branch/worktree:** `feature/fe-mobile-remediation`, `<local-machine-path>  
**Scope:** approved Plan Revision 41 / Addendum 67. No commit or push.

## M1 changes

- Updated the remaining Parent workflow screens to the current creative UI tone and shared components: Context, Handoff, Drawing Guide, Lesson Picker, Transcript Review and Sketch Guide. Existing route and API handlers were preserved.
- Tightened the story worker prompt so character/word-count targets stay internal. The worker rejects leaked count metadata with `STORY_COUNT_METADATA_LEAKED`; it does not silently remove text from a generated story.
- Corrected Modal call outcome logging: a successful remote call is no longer reported as an unknown worker failure only because its terminal log arrived after the initial log snapshot.

## Offline verification

| Check | Result |
|---|---:|
| `deployment/modal/srs_v23/tests/test_parent_story_output_contract.py` | 64 passed |
| `backend/tests/unit/test_modal_story_function_client.py` | 10 passed |
| `pnpm --dir apps/ui-mobile test` | 125 passed, 15 files; copy validator valid |
| `pnpm --dir apps/ui-mobile typecheck` | Passed |

These checks do not prove a fresh live Qwen response or video output.

## Emulator verification

- Before reload, the real Expo app showed the current purple Parent story screen, but the already-persisted story still contained trailing numeric fragments such as `68` and `69`. This saved revision was not rewritten or edited in the UI.
- The app was force-stopped and relaunched to verify the current bundle. It briefly showed a blank startup surface, then reached the Parent sign-in screen. Metro `/status` remained `packager-status:running`; the task API `/health` returned `200`. Filtered React Native/Android runtime error logs were empty.
- The authenticated Parent session did not resume after relaunch. No new account was created, no credentials were read, and no inference was triggered. Therefore the six changed workflow screens have offline/UI-source verification, but their post-reload authenticated visual verification is **incomplete**.
- Captures: `00-before.png`, `01-current-before-reload.png`, `02-after-reload.png`, `03-after-wait.png`.

## Video flow — product integration not complete

The live FEAT-081 task API `http://127.0.0.1:58100/openapi.json` contained **0 Parent video routes**, and its checked-out Parent router had no video operations. The FEAT-081 worktree's local Modal `video_app.py` was a fail-closed scaffold. That local-file finding does not describe the deployed Modal app: a later cross-worktree audit found the deployed LTX-2.5 worker and real output evidence in FEAT-067; see the correction below.

| Required dependency | Verified state |
|---|---|
| Parent video request/status/playback/complete/redo API | Missing from FEAT-081 served OpenAPI and current Parent router. FEAT-067 has request/status routes, but its service records a fail-closed unavailable result rather than dispatching. |
| Durable `story.video_generations` / `story.video_generation_scenes` mapping and lifecycle | Not present in FEAT-081. FEAT-067 has migration/persistence groundwork, but not a complete generation lifecycle connected to Modal. |
| Billing quota admission + AI Policy compute reservation | No usable Parent video admission/dispatch integration in FEAT-081; FEAT-067 returns `VIDEO_ADMISSION_DEPENDENCIES_UNAVAILABLE`. No quota bypass is used for product output. |
| LTX-2.5 Modal inference and deterministic silent composition | **Exists and has generated real candidates in FEAT-067.** The FEAT-081 checked-out `video_app.py` is still a scaffold and is not the deployed worker source. |
| Technical, scene-consistency and automatic video safety validation | No verified Parent video path to these gates |
| Private playback and post-video activity projection | No Parent video result route or validated asset to serve |

The exact server-owned story hash/adult confirmation was not re-read after the app restarted. More importantly, the saved story contains malformed count fragments, so it is not suitable for a video request even if its confirmation is valid. No video request was made from the FEAT-081 runtime. This is separate from the real Modal LTX candidates recorded by FEAT-067 below.

## Next dependency

Continue Parent product integration after the Billing/AI Policy admission adapter is available. Reuse the existing Modal LTX-2.5 worker and its candidate-generation contract; do not rebuild that worker. Keep the run fail-closed until the server can verify the exact confirmed script, source drawing and activity receipt, reserve real quota and compute, persist and dispatch the generation, and gate private playback.

## Correction — Modal LTX worker audit (2026-11-20)

The initial Rev41 assessment incorrectly generalized the FEAT-081 local scaffold to the whole system. The Modal `dev` app `sketch2life-srs23-dev-video` is deployed (v1, deployed 2026-11-18) and exposes seven functions, including `generate-silent-story-video` and `generate-video-scene` on L40S. The matching full worker source is in the separate FEAT-067 worktree at `deployment/modal/srs_v23/video_app.py`.

FEAT-067 contains actual LTX-2.5/L40S output evidence: attempt 12 produced a silent five-scene, 30-second, 1280×720 MP4 candidate in 440.725 seconds and passed technical media validation; attempt 14 also produced a technically valid candidate, but its visual review failed because the leaf placement/shape and some sampled content did not follow the story. Neither candidate passed automated child-safety validation, private asset promotion, or product playback. Evidence is in `<local-machine-path> and its `attempt_12/` and `attempt_14_corrected_cold/` directories.

This does not make Parent video end to end. FEAT-067 has Parent video request/status routes, but its current `ParentVideoGenerationService` records a fail-closed `VIDEO_ADMISSION_DEPENDENCIES_UNAVAILABLE` outcome rather than dispatching to Modal. Its video candidate test called Modal directly after confirming a synthetic story, bypassed product admission, and deliberately left safety/playback incomplete. The FEAT-081 mobile client still has no video-generation request/status operations. At the time of the FEAT-081 check, its served API also exposed no Parent video route.

Current Modal state at this audit: the app is deployed with zero live tasks. No deploy, GPU call, quota mutation, or app stop was performed for this correction.
