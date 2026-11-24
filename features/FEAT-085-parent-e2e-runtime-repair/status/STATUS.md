# FEAT-085 status

- **Current status (2026-11-24):** Real Parent workflow generated a candidate with Modal and playback was verified on Android from the existing candidate. No new video request was sent during playback verification.
- **Plan:** Rev1 approved by the owner's direct end-to-end repair request.
- **Implementation:** Fixed the confirmed mobile syntax error at `useParentController.ts:618`; aligned the existing API contract test with required request IDs; added dev-only logging of the auth API origin/path. Port `58000` belongs to a different worktree and forces Auth Emulator mode. Port `18000` verifies real Firebase but lacks the current completion endpoint. Its old database references an Alembic revision absent from this branch, so it will remain untouched. A current-branch backend image is built; its task Compose stack is being isolated from those older services.
- **Verification:** Earlier focused checks remain recorded below. The latest continuation passed real activity suggestion/selection, Qwen3.8 story generation and adult confirmation, LTX-2.5 inference for all five scenes, silent composition, final media validation, UI candidate-ready state, and Android playback to 0:08 / 0:30. LTX checkpoint access passed after the owner's second Secret replacement and the 71.1 GB pinned checkpoint was staged. The candidate is 30 seconds, five scenes, no audio.
- **Evidence:** `evidence/ANDROID_PARENT_E2E_20261123/01-redbox-bundle-error.png` captures the initial parser error; `02-after-bundle-reload.png` captures the repaired login screen. Do not treat the former as current UI.
- **Security follow-up:** A Firebase Admin base64 credential value was inadvertently exposed in an earlier tool output. Rotate/revoke that key; its value is not recorded here.
- **Earlier runtime snapshot (2026-11-23):** User switched Modal workspace. The selected profile `hieuptse184252` was reachable but had no deployed apps/model volumes. The FEAT-085 API still had the old `anhkhoa14155` workspace credentials; a real UI activity request failed before worker creation with `ResourceExhaustedError`, and a CPU probe identified that old workspace as disabled. Addendum 2 approved provisioning the minimum Qwen3.8/LTX-2.5 resources in the selected profile and switching only the task API runtime in memory, preserving the root `.env`. This blocker was resolved in the later run recorded below.

## Final continuation result — 2026-11-23

The final run details, call references, stage times, screenshot links, Modal cleanup, and playback continuation are in [`../evidence/RESULTS_PARENT_E2E_AFTER_HF_TOKEN_UPDATE_20261123.md`](../evidence/RESULTS_PARENT_E2E_AFTER_HF_TOKEN_UPDATE_20261123.md). The post-worker Android screenshot is [`../evidence/runtime/parent-video-after-worker.png`](../evidence/runtime/parent-video-after-worker.png); verified playback is [`../evidence/runtime/parent-video-playback-confirmed-20261124.png`](../evidence/runtime/parent-video-playback-confirmed-20261124.png). Exact Modal video and language/audio apps used were verified stopped with 0 tasks; the staged volume and unrelated apps were kept. No commit or push.

## Playback verification — 2026-11-24

- Logged into the existing synthetic Parent account through ADB using local root `.env` values; credentials were not copied to evidence.
- Resumed the existing run `c8ab4140-739e-496f-8b11-1c58e4a857a3`.
- The current-candidate API returned the existing ready candidate; the authenticated preview opened in the mobile player.
- Pressed Play and observed the timer advance to **0:08 / 0:30**, with a changed frame and the **Tạm dừng** control.
- No video POST, AI inference, quota bypass, or safety bypass occurred during this continuation. Modal inference apps remained stopped.
- The story screen showed a stale activity-selection warning despite story confirmation; it did not block playback and is a separate UI-state inconsistency.
