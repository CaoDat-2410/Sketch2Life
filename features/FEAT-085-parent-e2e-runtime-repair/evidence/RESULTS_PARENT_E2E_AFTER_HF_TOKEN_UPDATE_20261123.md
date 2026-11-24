# Parent E2E result after Hugging Face token update

**Date:** 2026-11-23 (generation run); playback follow-up 2026-11-24 (Asia/Saigon)
**Run:** `c8ab4140-739e-496f-8b11-1c58e4a857a3` (synthetic/development data)
**Path:** Android Expo UI → isolated FEAT-085 backend → Modal Qwen3.8/LTX-2.5
**Verdict:** AI generation, backend/UI readiness, and Android playback passed. Playback was verified on 2026-11-24 using the already-generated candidate; no new generation request was sent. No fixture responses, video retries, quota bypass, or safety-gate bypass were used.

## What ran

This resumed an existing synthetic Parent run already containing its drawing, confirmed subject, and context. No new drawing inference was sent in this retry. The optional curated SVG guide had no match and was skipped through the normal non-blocking UI path.

| Step | Result and evidence |
|---|---|
| Activity suggestions | Real Android request `a654e2ce-e33d-400e-bdaa-6a2f32eee258` reached Modal call `fc-01M84FA02D9YQ715563AB38MAB`. Qwen3.8 generated three fallback activities; the API persisted them and the parent selected the first. The activity API path succeeded. One content-quality observation: some materials lists were overlong/noisy; the selected activity itself had coherent child actions. See `parent-activity-result-3-final.png`, `parent-activity-selected-3.png`. |
| Story | One real UI request reached Modal call `fc-01M84G2DTWCRQZK2TKDSQAY8PD` (Qwen3.8-27B-FP8, L40S). Generation produced 1,225 tokens in 288.454 seconds; total request time was about 4m48s. The UI displayed a five-scene draft titled “Chú rùa xanh tìm dấu chân”. The adult confirmation action succeeded. Raw story text is not reproduced here. See `modal-story-generation.log`, `parent-story-after-completion.png`, and `parent-after-story-confirm.png`. |
| Hugging Face access | The first post-update preflight still returned HTTP 401. After the owner replaced the Secret again, the CPU-only preflight passed for `Lightricks/LTX-2.5`, pinned revision `49b093a39c19169a8a81721dcc541e07e945232f`. Evidence: `modal-ltx-access-preflight-after-secret-update-2.log`. No token value was read into this report. |
| LTX model staging | Download completed in about 7m03s: 5 files, 71,114,917,404 bytes (~71.1 GB). The Modal model volume was retained. `modal-ltx-model-download.log` and `modal-ltx-volume-status-after-download.log` record the result. |
| Video request | A single Parent UI `POST /v1/story-runs/c8ab4140-739e-496f-8b11-1c58e4a857a3/video-generations` returned HTTP 202. Modal call `fc-01M84HE5K6R6MPXAA3M2J63DMQ`; job `940ec98fd9fa9cf1`; generation `51f428bdb2cde2eb`; attempt `876434a748121918`. Model: LTX-2.5, pinned revision above, L40S. Story-manifest validation, GPU preflight, model load, all five scene generations, silent assembly, and final-media validation succeeded. Model load took about 9.7s; five scene inference times were 122.673s, 76.866s, 73.503s, 77.426s, and 76.762s; total worker time was 449.288s. The output is a 30-second, five-scene silent candidate. No narration or audio generation was requested. |
| Backend/UI result | The app polled the real current-generation endpoint successfully and displayed **“Video đã sẵn sàng”**, **“30 giây · 5 cảnh · Không có âm thanh”**, and an **“Mở video”** action. Screenshot/XML: `runtime/parent-video-after-worker.png` and `.xml`. This proves the backend/UI candidate-ready state, not successful playback. |

## Initial playback attempt — 2026-11-23

The emulator’s ADB server initially failed to start because port 5037 had stale server processes. Restarting the already-authorized ADB 5037 server restored the transport, but Android shell, `uiautomator`, `input tap`, and `exec-out screencap` requests stalled. An emulator-console tap was sent once to the visible “Mở video” control; a host-side screenshot then showed Android rebooting rather than a player. The app was later relaunched, but the console text-input path corrupted the local synthetic sign-in field and Firebase returned `INVALID_LOGIN_CREDENTIALS`; this was an input-entry failure and is not evidence of a backend credential regression. No further login or video request was sent.

At the time, the result was:

- **Video inference and candidate readiness: PASS.**
- **Actual player open/playback: NOT VERIFIED at the time of this initial attempt.** See the continuation below.
- **Video safety approval / production readiness: NOT CLAIMED.** The UI still marked the candidate as an unreviewed test result.

The ready-screen screenshot is `runtime/parent-video-after-worker.png`. Earlier transient emulator screenshots used for diagnosis remain outside repository evidence; no credentials or environment values were copied into the feature folder.

## Playback verification continuation — 2026-11-24

The Android emulator was recovered through ADB. The existing synthetic Parent account signed in from the local root `.env`; no credential values were written to evidence. The existing run `c8ab4140-739e-496f-8b11-1c58e4a857a3` was resumed from the Parent home screen.

The UI's current-candidate lookup (`GET /v1/story-runs/{run_id}/video-generations/current`) returned the already-generated ready candidate. The authenticated preview source opened, and pressing **Phát video** started the MP4 stream. Eight seconds later the UI showed **0:08 / 0:30**, the playback control had changed to **Tạm dừng**, and the turtle frame had advanced. This verifies candidate lookup, authenticated preview retrieval, Android decoding, and actual playback from the existing candidate.

Evidence: [`runtime/parent-video-playback-confirmed-20261124.png`](runtime/parent-video-playback-confirmed-20261124.png).

No POST to create a video candidate, AI inference, quota bypass, or safety bypass was performed during this continuation. Modal inference apps remained stopped. The story screen also displayed a “Chọn hoạt động chính trước khi tiếp tục” notice despite the confirmed story; it did not prevent the existing video candidate from opening or playing and should be tracked separately as a UI state inconsistency.

**Updated result:** Parent video playback on Android — **PASS**. Video safety review/production readiness remains unclaimed; the app correctly labels this as an unreviewed technical preview.

## Cleanup

In Modal profile/workspace `hieuptse184252` / `dev`, the exact apps used for video and Qwen language/story were stopped after inference. A fresh `modal app list --json` showed both app descriptions in `stopped` state with 0 tasks. Other Modal apps were not stopped. The model volume remains staged. Docker services were left running.

No application/backend/worker code changed in this verification retry. FEAT-085 status and evidence documentation were updated. No commit or push was made.
