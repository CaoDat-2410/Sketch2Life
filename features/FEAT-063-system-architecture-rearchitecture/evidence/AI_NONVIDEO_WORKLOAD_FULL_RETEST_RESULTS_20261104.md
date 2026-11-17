# EV-063-44 — Full non-video AI workload retest

**Date:** 2026-11-04 (Asia/Saigon)
**Status:** PARTIAL — authorized calls completed or ended at the approved 600-second queue bound; GPU-backed outputs remain blocked by Modal L4 capacity.
**Canonical product source:** FEAT-063 System Architecture SRS v2.3-draft. The SRS was not modified.
**Approved plan:** [`AI_NONVIDEO_WORKLOAD_FULL_RETEST_20261104.md`](../plan/AI_NONVIDEO_WORKLOAD_FULL_RETEST_20261104.md).

## Scope and guardrails

- Used synthetic butterfly artwork, synthetic narration, and a reviewed synthetic lesson fixture only.
- Did not call video generation, scene generation, video composition, or final video validation. `video_calls=0`.
- Did not enable any product workload. Every entry in `deployment/modal/srs_v23/workloads.json` remains `enabled: false`.
- No output was promoted beyond a private draft/POC. Unknown outcomes were not retried.
- Kept both shared Modal Volumes and all pre-existing shared Docker services.

## Implementation and alignment work

- Added the versioned Parent story-revision contract and persistence/API support, including exact age, adult-confirmed subject, image/context lineage, 5–15 ordered scenes, 30–90-second duration, contiguous timing, per-scene narration and visual prompts, and adult confirmation before downstream video admission.
- Added the narrow butterfly lifecycle guard and terminal error classification for known worker/schema/fact-check failures.
- Corrected the story adapter to use the language worker's `sketch2life.modal.ai-request.v1` manifest instead of the drawing worker's `sketch2life.modal.drawing-input.v1` manifest. The corrected worker request was called directly once in this retest; it remained queued and did not reach inference.
- Added a private Modal SAM 2.1 Hiera-Small feasibility handler, pinned to the official repository commit and checkpoint hash. The checkpoint downloaded and verified; the segmentation inference did not run.
- Updated the workload registry with observed retest outcomes. Product dispatch remains disabled.
- No Parent activity API or Teacher Deck HTTP/session API was added in this task.

## Runtime results

| Workload | Result | Observed time | Details |
|---|---|---:|---|
| `drawing.analyze` | `UNKNOWN_NO_RETRY` | 600 s bound | Parent API accepted the synthetic image, then returned `VISION_OUTCOME_UNKNOWN`. Run `78c41aed-af20-4d2d-8888-8787dc4306a2` remains `INPUT_PROCESSING` / `AWAITING_RECONCILIATION`, `retryable=false`, `OPERATOR_REVIEW`. Do not retry or reconcile automatically. A prior separate synthetic call had recognized a butterfly; that is historical evidence, not this retest's result. |
| `story.generate` / `storyboard.generate` | `UNKNOWN_NO_RETRY` | 607.451 s | One direct synthetic worker call with an adult-confirmed subject fixture waited for `GPU_L4`; Modal logs said it was acquiring capacity. No model output or API draft was produced. The positive Parent story-revision confirmation path remains unverified. |
| `parent.sketch-guide.generate` | `UNKNOWN_NO_RETRY` | 604.071 s | Generic topic/difficulty only; no child/profile/image data. No guide image was returned. A prior separate POC had succeeded. |
| `teacher.sketch-deck.generate` | `UNKNOWN_NO_RETRY` | 603.068 s | Fresh call waited for `GPU_L4`. A prior direct POC produced a 5-slide, 16:9 Vietnamese DRAFT with four drawing steps and two approved activities; this retest produced no new deck. |
| `lesson.visual.generate` | `UNKNOWN_NO_RETRY` | 608.026 s | Reviewed synthetic plan only. No visual asset was returned. |
| `drawing.segment` (SAM2 feasibility) | `UNKNOWN_NO_RETRY` | 602 s | Model checkpoint was downloaded and hash-verified; segmentation returned no mask. The original drawing was retained. |
| `tts.narration.generate` | **Succeeded** | 19.574 s | Synthetic Vietnamese WAV, 176,684 bytes. |
| `asr.transcribe` | **Succeeded** | 22.471 s | Whisper identified Vietnamese and transcribed the synthetic line exactly: “Con bướm bay qua khu vườn đầy nắng.” |
| `lesson.plan.suggest` | Not dispatched by design | — | SRS Q157/Q159 role/model selection remains unresolved. |
| Video workloads | Excluded | — | No video-related inference or composition call occurred. |

The repeated L4 scheduling messages make GPU capacity the concrete blocker for the fresh Qwen/FLUX/SAM2 attempts. The API correctly retained unknown jobs for reconciliation instead of fabricating a result or silently retrying.

## API, migrations, and tests

- Applied Alembic `upgrade heads` to three task-owned PostgreSQL databases: the Parent-flow run database, the API-contract database, and the focused-test database. The new story revision migration was included.
- Re-exercised all **13 mounted StoryRun-lite operations** through 14 HTTP contract checks. The checks passed, including expected `409`, `404`, and `422` rule responses; the upload flow reached `READY`. This contract run intentionally dispatched no AI.
- The separate Parent API flow exercised upload and image attachment. Its AI result ended unknown as described above; positive subject confirmation, positive story generation, and positive story confirmation were not reached.
- Focused Python 3.12 contract/integration/unit run: **46 passed; 2 deselected**. The two deselected PostgreSQL integration cases require a pre-migration legacy asset fixture (`STORYRUN_LITE_LEGACY_ASSET_REF`) that this task database did not contain. A separate post-format run of the two AI/story client unit files passed **10 tests**.
- Targeted Ruff checks on changed backend/Modal files passed. `compileall` passed for backend source, unit tests, Modal workers, and evidence scripts. `git diff --check` passed; Git emitted only its existing CRLF normalization notices.
- Initial test-environment errors were harness-only: one run mounted only `backend/` and therefore could not find the FEAT-063 OpenAPI snapshot; another used a latest-schema database for tests that require a legacy pre-migration fixture. The correct full-repository mount passed the non-fixture-dependent cases. No security guard was weakened.

## API availability and remaining gaps

- The mounted Parent StoryRun routes have passing contract coverage, but the live AI success path is blocked at image understanding. The story-revision create route's positive AI path and the adult-confirmation success path remain unverified.
- The isolated StoryRun-lite HTTP app does not mount Parent Sketch Guide, Teacher Sketch Deck create/read/present, or Parent post-video outdoor-activity list/selection endpoints. Those Modal functions were called directly where allowed; direct worker success is not equivalent to an HTTP workflow.
- `/health` and `/openapi.json` are not mounted in this isolated StoryRun-lite app; their `404` is a harness boundary, not a product API regression.
- `lesson.plan.suggest` remains intentionally unavailable pending the SRS owner decision. Video processing was not tested under this scope.

## Evidence and shutdown

- Per-call dispatch records, output/result JSON, timing, and synthetic artifacts: `evidence/assets/ai_nonvideo_full_retest_20261104/`.
- Full Parent/API traces: `poc_run_trace.json` and `api_contract_non_ai_v2_results.json` in that folder.
- Fresh speech round-trip: `speech_roundtrip_summary.json` and `synthetic_vietnamese_narration.wav`.
- SAM2 checkpoint attestation and inference result: `sam2_checkpoint_download_result.json` and `sam2_segment_result.json`.
- All four currently deployed Modal `dev` apps (language/audio, drawing VLM, FLUX, and SAM2) were stopped. Final Modal inventory shows every app record `stopped` with `0` tasks; older duplicate app records were already stopped.
- Task PostgreSQL container was stopped and auto-removed; task port 5434 was closed. The disposable pip-cache volume was removed. Shared Docker API/PostgreSQL/Redis/ClamAV services remain running and untouched.
- Model/scratch Modal Volumes and synthetic evidence were retained. No commit or push was performed.
