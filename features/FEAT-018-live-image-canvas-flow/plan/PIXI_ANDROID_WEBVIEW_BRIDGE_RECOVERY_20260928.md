# Pixi Android WebView bridge recovery

- Status: APPROVED
- Plan revision: 1
- Implementation status: implemented and offline-verified; fresh-session Android smoke acceptance remains pending because the observed demo session expired
- Feature: FEAT-018 live image and canvas flow
- Approval source: project owner’s direct request in this conversation to inspect backend logs and fix the persistent Pixi loading bug

## Goal

Make the Android native-to-WebView Pixi launch/control bridge deliver validated messages reliably, and ensure the app reports renderer readiness only after it receives an actual renderer response.

## Evidence and diagnosis

During the owner-reproduced Android flow, the local backend recorded successful session creation, image admission, understanding, Gate A, P1, Gate B, and `/renderer/launch` (all 200/201). The renderer HTML loaded (200) and its hashed JavaScript chunks were served from cache (304). The backend recorded no subsequent reads of `/v1/renderer/source`, `/v1/renderer/rig-package`, or `/v1/renderer/rig-mask`, while the app showed the Pixi loading timeout. A retry repeated the bootstrap/status behavior without issuing those reads.

This isolates the failure after the backend launch response and Pixi page bootstrap but before the launch command is consumed by the WebView. The current mobile host counts a repeated bootstrap plus a cached command as renderer-ready even though it has not received a playback/lifecycle response. No Qwen, SAM, Lightning, backend endpoint, or public contract change is required for this slice.

During emulator retry after rebuilding the hashed renderer bundle, the cached page shell requested removed asset names and received 404. Retries currently reuse the same renderer page URL, so the page shell can remain stale even when the backend serves a newer build.

The WebView page also applies the 4 KiB renderer-event limit to inbound launch commands. The emulator page reports that its launch exceeded the bridge limit before issuing any source/package read. Keep the 4 KiB event cap and give schema-validated native-to-page commands a separate 128 KiB ceiling, matching the bounded V2 animation-track contract.

After the launch-size fix, the renderer reached `GET /v1/renderer/source` but received 404. The backend issues source and package capabilities with a 90-second TTL, and source reads consume a bounded grant. The app’s manual retry reused its original launch payload, so an explicit retry after the deadline could only reuse expired capabilities. Each explicit retry must request a fresh launch/capability from the existing Gate-B-approved session before remounting Pixi. In the current API composition, scene localization is disabled; the launch retry uses the existing deterministic template package path and must not call Qwen/SAM/Lightning.

## Scope

1. Replace the ambiguous Android WebView native `postMessage` delivery for Pixi launch/control commands with an explicit JavaScript bridge function invoked through the WebView’s `injectJavaScript` API after the page emits its bootstrap. Keep renderer-originated event messages capped at 4 KiB and use a separate 128 KiB ceiling for schema-validated native launch/control messages.
2. Keep renderer-side JSON, byte-size, schema, and `rendererInstanceId` validation; preserve the startup gate’s one-launch/idempotent behavior and bounded replay on bootstrap.
3. Separate “page bootstrap received” from “renderer accepted/started launch” in the mobile state machine. Only a valid playback or lifecycle response can mark launch readiness; bootstrap alone must not extend/mislabel readiness.
4. Keep failures visible and recoverable, preserve the source image and manual retry, and keep playback controls on the same validated bridge path.
5. Give each explicit renderer retry a fresh page URL so a cached HTML shell cannot refer to removed hashed bundles; preserve normal cache reuse for content-addressed assets.
6. On explicit user retry only, refresh the existing renderer launch so short-lived source/package capabilities are renewed before WebView remount. Do not add automatic launch/provider retries or call Qwen/SAM/Lightning in this path.
7. Add focused bridge/state regression coverage and feature-local evidence.

## Non-goals

- No backend or Lightning endpoint/model changes; no Qwen/SAM calls or provider credentials.
- No renderer visual redesign, new visual assets, animation-plan change, image/mask contract change, session persistence, video work, or unrelated workflow changes.
- No automatic replay of provider or session-preparation operations.

## Acceptance criteria

1. A fresh Android Pixi launch receives the backend-issued command in the WebView and triggers a successful source-art read; a V2 launch also reads its rig package and reads a mask only when the validated command requires one.
2. The app does not report the renderer ready merely because it received a duplicate bootstrap. It enters ready/playback state only after a matching renderer-instance response.
3. If the WebView rejects or fails the launch, the app reaches a clear retryable failure state rather than remaining indefinitely on “Đang mở…”.
4. PLAY, PAUSE, REPLAY, and seek controls are delivered through the same validated bridge and remain instance-bound.
5. A renderer retry requests a fresh page-shell URL and does not request removed/old hashed bundle filenames.
6. An explicit retry refreshes the launch and its expiring capabilities once before remount; it does not trigger on page bootstrap or silently loop. A fixture contract regression proves a second renderer launch on the same approved session issues fresh source/package capabilities without increasing provider-call count.
7. Existing V1/V2 contracts, original-image preservation, capability/hash checks, startup-gate duplicate suppression, and fallback behavior remain intact.
8. Focused unit/type/build checks pass, and an Android emulator smoke test shows actual playback progress or an explicit safe fallback/failure. Backend logs confirm the source/package reads for the reproduced session; no live AI call is made.

## Risks and mitigations

- Injected JavaScript can be malformed if message content is interpolated unsafely. Serialize the entire message as a JSON string literal, keep the existing byte limit, and test escaping.
- A page reload can replay a launch. Preserve the renderer instance ID, startup gate, and exact cached launch; duplicate delivery must remain idempotent.
- Backend success can coexist with renderer failure. Preserve explicit renderer acknowledgment/state and do not infer success from transport status.

## Verification plan

1. Add deterministic tests for safe native-to-renderer bridge script construction and renderer-message validation/idempotent replay.
2. Add/run an offline backend contract test that repeats the renderer launch after Gate B, validates new source/package capability reads, and confirms no new model/provider call.
3. Run art-renderer unit tests, typecheck, and Vite build.
4. Run mobile TypeScript validation, UI regression checks, and Android Metro bundle/export checks available in the current workspace.
5. Reload the already-connected Android emulator and exercise the Pixi launch and controls; inspect the attached backend session log for source/rig capability reads and capture a feature-local screenshot/evidence note.
6. Run `python tools/validate_repository_security.py` before any commit (no commit is included in this plan).

## Evidence plan

Record the backend log excerpt without secrets/media, commands and results, emulator identity, timestamp, observed UI state, and any remaining limitation under `evidence/notes/PIXI_ANDROID_WEBVIEW_BRIDGE_RECOVERY_20260928.md`. Do not store the child drawing or credentials in the feature folder.

## Implementation outcome — 2026-09-28

- Implemented the bounded native-to-WebView bridge, distinct 128 KiB command limit, renderer-instance-bound readiness, fresh page-shell URL per manual retry, and explicit launch/capability refresh on retry. Renderer-originated events remain capped at 4 KiB; no backend production code or provider call was added.
- Added a same-session offline backend contract regression proving renderer source/package grants can be renewed and read without an additional vision/provider call.
- Offline checks passed: art-renderer tests (36/36), renderer typecheck and demo build, mobile TypeScript check, UI recovery validation, and the focused backend renderer-launch renewal contract test. See the feature-local evidence note for commands/results.
- Live Android acceptance is not claimed. The observed first retry reached the source endpoint but its 90-second capability had expired; the explicit renewal then reached `/renderer/launch` after the in-memory session itself had exceeded its 30-minute idle TTL and returned 410. A new owner-started flow is required to verify fresh-session source/package reads and playback. No AI/provider request was initiated by Codex.
- Scope and approved behavior are unchanged. The original approved plan hash remains recorded in `approvals/TASK_APPROVAL.md`; the final plan hash is recorded there as execution metadata.
