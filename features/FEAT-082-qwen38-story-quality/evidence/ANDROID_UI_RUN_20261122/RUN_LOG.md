# Parent Android real UI run — 2026-11-22

## Result

**Amendment J E2E completed through video playback on Android using synthetic data.** The final pass completed drawing analysis, Qwen3.8 activity fallback, story generation and one adult-directed rewrite, adult confirmation, LTX-2.5 video generation, status polling, and full 30-second playback. Earlier sections below retain the chronological failure/fix history; the final Amendment J section supersedes their then-current “pending/no video” status. The generated video is a synthetic development preview and is explicitly not safety-cleared.

## Model selection and the Modal volume screenshot

The screenshot was taken in the correct Modal account, `anhkhoa14155`, before the Qwen3.8 download had been staged in that account's volume. The volume now lists both `qwen3_5_9b` and `qwen3_8_27b_fp8`:

- Shared text/story workloads use `Qwen/Qwen3.8-27B-FP8@c3a462cc3d38cf351f3b26cbd763469eeb74ef81`.
- Drawing-VLM image understanding remains on `Qwen/Qwen3.5-9B@c202236235762e1c871ad0ccb60c8ee5ba337b9a` by design.
- The old Qwen3.5 folder is retained; it was not replaced or deleted.

## Parent flow evidence

| Step | Result | Evidence |
|---|---|---|
| Parent login and profile | Synthetic profile `May`, 60 months | `08-parent-home.png`, `09-profile-created.png`, `10-profile-selected-home.png` |
| Choose topic/subject and synthetic drawing | Topic `Thiên nhiên`, subject intent `Chiếc lá`, synthetic turtle-and-leaf artwork attached | `11-topic-selection.png`, `13-artwork-preview.png`, `14-artwork-attached.png` |
| Malware scan | First attempt failed before AI because the older stack owned host port 3310. With the approved temporary test-only port override, ClamAV joined the FEAT-082 network and scanned the same synthetic image `OK`; no malware gate was bypassed. | `16-clamav-network-error.png`, `17-clamav-ready-before-ui-retry.png` |
| Drawing VLM | Success, HTTP 200, Modal call `fc-01M81KK87X5J1C6GJKVE9YGCWY`, elapsed 37.499 s. Qwen3.5-9B recognized `con rùa và chiếc lá`; the adult confirmed the subject. | `18-drawing-retry-submitted.png`, `19-after-drawing-analysis.png`, `20-subject-confirmed.png` |
| Accessible lesson catalog | Zero accessible published/shared lessons and zero age-eligible activity candidates. | `21-activity-selection.png`, `22-activities-loaded.png` |
| AI fallback activity suggestion | One allowed request; terminal worker failure detailed below. No candidate was returned or selected. | `23-activity-suggestion-wait.png`, `24-activity-worker-failure.png` |
| Story/video | Not called. The required primary activity was not available for adult selection. Video is also outside this run's approved scope. | No story/video output |

## Activity inference failure

- **StoryRun:** `d8f8e127-a601-4676-b885-81373b239bfe` (synthetic test run).
- **Backend request:** `03319993-7818-4bed-808b-02d63f4abf6f`.
- **Modal call:** `fc-01M81MB5G7XZJ0ZG4GHPNFRSPJ`.
- **Worker/model:** `parent.activity.suggest`; `Qwen/Qwen3.8-27B-FP8@c3a462cc3d38cf351f3b26cbd763469eeb74ef81`; L40S.
- **Model load:** approximately 5.127 s, then failed during `fp8_kernel_allowlisted_load` in approximately 0.032 s; output tokens: 0.
- **Terminal code:** `MODAL_WORKER_FAILED_TERMINAL`.
- **Sanitized exception:** `httpx.LocalProtocolError: Illegal header value b'kernels/0.17.3; hf_hub/1.32.0; python/3.11.12; '`.
- **Cause:** the worker image sets `HF_HUB_DISABLE_TELEMETRY=1`; `kernels==0.17.3` then constructs an empty user-agent, and `huggingface_hub==1.32.0` formats it with a trailing separator. `httpx` rejects that header before any activity output. This is not a GPU allocation timeout, missing model, parser/quality-gate rejection, or story-prompt error.
- **Raw prompt/image/user data:** not retained in this report.

## Narrow remediation and checks

The approved worker now temporarily enables only generic package/runtime user-agent metadata while loading the exact pinned and allowlisted FP8 kernel, then restores the prior telemetry flag in `finally`. No request, profile, child, image, prompt, or generated-content data enters the user-agent.

- New offline tests verify the exact repo/revision/allowlist and restoration of the telemetry flag on success and failure.
- Focused Modal contract file: **78 passed**. Default pytest temp discovery initially hit a Windows access-denied error in the shared user temp root; rerunning with a worktree-local basetemp passed all 78.
- `py_compile`: passed for the changed worker and focused test.
- `git diff --check`: passed; Git printed only pre-existing CRLF normalization warnings for unrelated files.
- Deployed CPU `check_qwen38_decoder_readiness`: **ready**, Transformers 5.22.1, LM Format Enforcer 0.11.3. This checks deployed package/schema imports, not live FP8 kernel loading or model inference.
- Modal language/audio app was stopped after the check. `modal app list` showed its language/audio apps stopped with zero tasks; drawing and video apps were left untouched.
- The temporary ClamAV Compose override was removed. The Docker test stack is left available; no persistent volumes or database rows were deleted. The test emulator and this worktree's Expo processes were stopped.

## Next action from the earlier run (superseded by Amendment J outcome below)

Amendment J authorizes continued full Parent E2E with at most one new request after each distinct defect is fixed. The follow-up UI request loaded Qwen3.8 and passed the earlier kernel-bootstrap issue, then hit the next runtime incompatibility: Triton 3.3.1 lacks `triton.tools.tensor_descriptor`. The worker is being rebuilt with the supported PyTorch 2.8 / Triton 3.4 package set; do not send another inference until deployment/readiness confirms that API.

## Amendment J continuation — Triton descriptor incompatibility

- **UI action:** Parent Android UI requested the catalog-empty activity fallback for the existing synthetic StoryRun; no direct Modal call or fixture was used.
- **Backend request:** `def15576-132c-4670-b4e6-bc69662f315a`.
- **Modal call:** `fc-01M820QHK486RV7GGZYAHFNGYN`.
- **Model:** `Qwen/Qwen3.8-27B-FP8@c3a462cc3d38cf351f3b26cbd763469eeb74ef81`, L40S.
- **Progress:** Model load completed in about 5.156 seconds. The exact allowlisted FP8 kernel then failed while importing `triton.tools.tensor_descriptor`; zero generated tokens and no activity candidates were returned.
- **Root cause:** Triton was pinned at 3.3.1, but the pinned FP8 kernel uses the `TensorDescriptor` host API present in Triton 3.4. The previous compatibility work only repaired import aliases and autotuner constructor differences; it could not add the missing compiler/runtime descriptor implementation.
- **Fix:** Pin the aligned PyTorch 2.8.0 / torchvision 0.23.0 / Triton 3.4.0 stack and the official `causal-conv1d` 1.7.0 Torch 2.8 wheel (`sha256:b28c3657a9d6855e1f95bc912ab94f893434276b437dec8008c92c9f38b6a1f4`). Remove the no-longer-needed autotuner shim and add a stable descriptor-availability check.
- **Offline verification:** Focused Modal contract tests **82 passed**. Live Modal build/readiness and the next distinct UI request are pending. No story or video has been generated yet.

## Amendment J continuation — runtime telemetry call-site TypeError

- **Deployment routing correction:** The first deploy command was mistakenly run from the repository root, whose Modal worker source was stale. Backend readiness still reported the old package stack. Token fingerprints (never the token values) confirmed the API container is configured for `anhkhoa14155`; the defect was the deploy working directory. The corrected deployment was then run from this `feature/fe-mobile-remediation` worktree and Modal showed the deployment under `anhkhoa14155/dev`.
- **Readiness:** Invoked through the running API container's configured Modal credentials. Result: `torch=2.8.0`, `torchvision=0.23.0`, `triton=3.4.0`, `tensor_descriptor=ready`, `transformers=5.22.1`, `lm-format-enforcer=0.11.3`.
- **UI action:** One real Android UI tap on “Thử lấy gợi ý lại” after readiness. No direct worker call, no fixture, no repeat.
- **Backend request:** `86506fff-f49d-475a-bb23-6db461764ab4`; StoryRun remains `d8f8e127-a601-4676-b885-81373b239bfe`.
- **Modal call:** `fc-01M822DBTYEVS0Q7RGZ3BM6HYE`; job `e72ef12793066f58`; attempt `432a285315a9e1fa`; workload `parent.activity.suggest`; Qwen3.8-27B-FP8 pinned revision; L40S.
- **Progress:** scratch input uploaded in 1.287s; worker started; checkpoint verification 0.328s; model load 5.043s; FP8 runtime check passed; allowlisted kernel loaded in 1.826s. Generation did not start; output tokens: 0.
- **Terminal error:** `TypeError: 'NoneType' object does not support the context manager protocol`, at `_load_text_model` on `with worker_runtime_verified(...)`. The telemetry emitter returns `None`; it is a function call, not a context manager. This is not a model/kernel failure or timeout.
- **Fix:** Call `worker_runtime_verified(...)` directly while preserving the same allowlisted runtime metadata. Added an AST regression assertion in the focused test.
- **Offline verification:** Focused Modal contract file **82 passed**; `py_compile` and scoped `git diff --check` passed.
- **Evidence:** `49-activity-request-after-correct-deploy.png`, matching UI XML, and `ACTIVITY_INFERENCE_FAILURE_RUNTIME_TELEMETRY_CONTEXT_MANAGER_20261122.json`.
- **Next:** Redeploy from this worktree, repeat readiness via the backend container, then use at most one fresh real UI activity request for this distinct call-site defect. No story/video yet.

## Amendment J — final real Parent E2E outcome — 2026-11-23

### Runtime and completed flow

- **Device/UI:** Android emulator `emulator-5562`; package `com.sketch2life.parentexpo.qwen38test`; real Expo Parent UI and the running `s2l-feat081-rev23` API stack. No preview harness, fixture, direct worker invocation, or database state mutation was used.
- **StoryRun:** `d8f8e127-a601-4676-b885-81373b239bfe`, synthetic Parent profile/artwork only.
- **Drawing analysis:** Qwen3.5-9B Modal call `fc-01M81KK87X5J1C6GJKVE9YGCWY`, HTTP 200, 37.499 s; recognized the turtle and leaf and the adult confirmed the subject.
- **Activity selection:** the accessible published/shared catalog returned zero eligible candidates, so the UI used its AI fallback. Request `8564847d-ee0c-4f1b-a7de-bacb35ed9268`, Modal call `fc-01M822XW6J5CGC3P7059649GT5`; Qwen3.8-27B-FP8 on L40S returned three schema-valid suggestions in 275.668 s (generation 161.4 s). The adult selected one through the UI and the selection was persisted.
- **Story revision 1:** request `3975c22c-bd85-4134-922d-fd46fc9ad065`, Modal call `fc-01M823AZ27P4YEGKVA04NG4G0X`; Qwen3.8 produced five scenes in 314.938 s. The first draft introduced water and treated the leaf as a raft, so it was not accepted as-is.
- **Story revision 2:** the adult used the real UI rewrite field once to keep the turtle on land beside the leaf and remove the invented water. Request `3cad6c03-ea1e-4a05-b676-44598d73ef3d`, Modal call `fc-01M823Y9Q1JCM8PCXJRN47XFM5`; five scenes, parser/business validators passed, 326.44 s. The adult then confirmed this revision in the UI.
- **Video:** one UI request dispatched Modal call `fc-01M824GGG880MHYPXCWQ3Y757V`. Worker reported `worker_succeeded`, model `Lightricks/LTX-2.5`, revision `49b093a39c19169a8a81721dcc541e07e945232f`, GPU L40S, elapsed 450,330 ms. All five scene inferences completed (116.748 s, 77.722 s, 80.194 s, 84.378 s, 72.887 s); silent composition and final technical media validation succeeded. UI showed “Video đã sẵn sàng”, 30 seconds, five scenes, no audio. Playback was opened from the UI and allowed to reach 0:30.

### Evidence

- Story rewrite and adult confirmation: `65-story-rewrite-request.png`, `66-story-rewrite-result.png`, `68-story-adult-confirmation.png`.
- Video request and state progression: `70-video-request-sent.png`, `71-video-status.png`, `73-video-status.png`, `74-video-progress.png`.
- In-app playback: `75-video-playback.png`, `76-video-playing-start.png` (0:02), `77-video-playing-mid.png` (0:10), `78-video-playing-late.png` (0:18), `79-video-end.png` (0:30).
- `69-video-request.png` is the unchanged pre-request screen: an earlier tap used stale screen coordinates and landed outside the button; it did not dispatch a request. The one actual video request was the subsequent correct UI tap.
- Modal call ID and phase durations above came from that exact function call's worker logs; only allowlisted metadata was retained. No prompt, image bytes, credentials, or raw child data were copied into this report.

### Outcome and remaining limits

- **Technical Parent E2E:** pass through full silent candidate playback. No terminal API/Modal error remained in the final activity, story, or video passes. The worker runtime fixes and the 82 focused Modal contract tests are recorded above.
- **Activity catalog:** no eligible published/shared activity was available for this profile/topic; the documented AI fallback worked and persisted the adult's selection.
- **Story quality:** the initial draft needed one permitted adult-directed rewrite; the revised story was accepted and confirmed.
- **Video visual quality:** the source turtle/leaf drawing, colors, and crayon-like texture remain recognizable and both entities are visible. Review screenshots show a transient garbled text-like artifact in the early scene and relative-position drift/overlap between turtle and leaf in middle scenes. This is a quality limitation, not a generation/API failure; the candidate is not approved as a production-quality result.
- **Safety/product boundary:** Android UI explicitly labels the output “Bản thử nghiệm · Chưa kiểm tra an toàn.” No safety gate was bypassed. This candidate does not prove the SRS automatic frame/transcript/subtitle safety gate passed or that production playback is ready. The task-specific run was silent; canonical SRS BR-24's narration/subtitle target remains separate and is not satisfied by this silent preview.
- **Cleanup:** stopped the `emulator-5562` test emulator, the worktree Expo server, four `s2l-feat081-rev23` containers (API, PostgreSQL, MinIO, ClamAV), and the Modal video/language-audio/drawing apps. Modal app list confirms all three stopped with zero tasks; `docker ps` confirms the FEAT stack is stopped while the other running Compose stacks remain up. Containers/volumes were not deleted; no persistent data was removed.
