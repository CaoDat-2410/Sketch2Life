# FEAT-087 status

**State:** M0–M2, M4 and the offline part of M5 are done. M3's emulator check, M6 and M7 are blocked.
**Plan:** `plan/DESIGN_REV1_SUBJECT_ROLES_KEYFRAME_VIDEO.md`
**Approval:** `approvals/TASK_APPROVAL.md`

| Milestone | Status | Evidence |
|---|---|---|
| M0 LTX multi-image / end-frame check | Complete | `evidence/M0_LTX_MULTI_IMAGE_END_FRAME_20261124.md` |
| M1 Recognition v2 (main + 0-3 secondary, label, features, 20x20 box grid) | Complete | Worker and backend unit tests |
| M2 Parent roles API (review and edit roles) | Complete | Backend unit tests |
| M3 Mobile roles UI | Code and vitest done; **emulator check blocked** | Metro is not running on the user's Windows host. Start it with `EXPO_PUBLIC_FEAT081_VISUAL_PREVIEW=true`, then re-run the adb-mcp check. |
| M4 Per-scene staging (`sketch2life.story-staging.v1`) | Complete | `test_story_staging*.py`, `test_modal_story_function_client.py`, `test_story_staging_worker.py` |
| M5 Keyframe compositor, SAM masks, LTX end-guide, prompt `story-i2v-v8`, backend keyframe plan | Complete offline | Modal suite 332 passed; backend FEAT-087 tests pass. Synthetic keyframes in `evidence/M5_keyframes_synthetic/`, eval drawings in `evidence/eval_set/`. |
| M6 Live spike (SAM edge quality, `.guide` strength 1.0 vs 0.8, memory with SAM + LTX) | **Blocked** | This VM has no Modal credentials (`~/.modal.toml` and `MODAL_*` are absent). |
| M7 Three live videos plus before/after report | **Blocked** | Depends on M6. |

## What offline tests do not prove
- SAM mask edge quality on real crayon drawings.
- The `ImageConditioningInput.guide` strength at the end frame.
- Memory headroom with SAM and LTX in one warm L40S container.
- The paper-fill look when a real mask is removed.

A4 (sprite in K(i) pixel-identical to the original) is tested on synthetic drawings only. Nothing has been rendered by LTX.
