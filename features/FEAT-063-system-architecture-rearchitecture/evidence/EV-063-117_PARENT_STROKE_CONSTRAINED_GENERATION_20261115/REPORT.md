# Rev87.21 — Parent constrained stroke generation

**Date:** 2026-11-15<br>
**Status:** PARTIAL — all three permitted calls completed; no valid guide returned.<br>
**Model:** Qwen/Qwen3.5-9B, revision `c202236235762e1c871ad0ccb60c8ee5ba337b9a`, Modal `dev`.<br>
**Input:** generic synthetic topic `con mèo`; no child profile/photo/voice/consent/personal data, no video.

## Outcome

The fixed-key internal decoder shape corrected the prior incomplete stroke array: the worker normalized the required stroke objects and reached geometry validation. Follow-up prompt changes reduced the number of emitted records from 12 to 8 and added distinct-part wording, repeated-feature detection, and safe duplicate diagnostics. Despite these corrections, all three live responses were rejected by unchanged hard gates:

1. **Call 1:** Qwen emitted duplicate geometry by stroke 5 (four unique geometries before rejection), HTTP 502 after 193.140 s.
2. **Call 2:** Qwen produced eight unique geometries, then a duplicate at stroke 9 in the 12-record configuration; a feature label also repeated. HTTP 502 after 211.341 s.
3. **Call 3:** the 8-record configuration passed duplicate checks up to the first record, but its path failed `SVG_CONSTRUCTION_GUIDE_STROKE_COMPLEXITY_INVALID`. That path was 768 characters; the safe log did not include its command count, so the exact subcondition cannot be stated. HTTP 502 after 446.930 s.

These are model output/geometry-contract failures, **not API reachability failures or worker timeouts**. No call returned an API guide, valid SVG, or render. No fixture, repaired output, or quality-gate bypass was used. Rev87.21's three-call cap is consumed; no fourth inference was sent under this plan.

## Runtime attempts

| Call | Request / Modal call | API elapsed | Worker inference | Terminal result |
|---|---|---:|---:|---|
| 1 | `5827e78b-874b-42b2-a688-7494ac67fded` / `fc-01M7ES2HPGZQPZSR8T9DEZ75NP` | 193.140 s | 106.086 s | `SVG_CONSTRUCTION_GUIDE_GEOMETRY_COMPLEXITY_INVALID`; 4 unique strokes, duplicate at stroke 5; 4 stages; 264 geometry chars. |
| 2 | `70800874-b993-4e8c-b07e-dc7b617cf099` / `fc-01M7ESHB451WMXQQXJN3NM8GWY` | 211.341 s | 133.413 s | `SVG_CONSTRUCTION_GUIDE_GEOMETRY_COMPLEXITY_INVALID`; 8 unique strokes, duplicate at stroke 9; 4 stages; 1,191 chars; 2,627 output tokens. |
| 3 | `ed1ea9e0-3464-4428-9517-a06168313227` / `fc-01M7ESW77FDEXFPWQR8YFJPF7B` | 446.930 s | 369.934 s | `SVG_CONSTRUCTION_GUIDE_STROKE_COMPLEXITY_INVALID`; first stroke reached 768 chars; 4 stages; 6,908 output tokens. |

Across the three calls, route wait totaled 851.411 seconds and recorded model-inference time totaled 609.433 seconds. The model loaded successfully each time (about 18–22 seconds); catalog lookup and worker startup also completed. Each API failure occurred after inference and during strict output validation.

## Code and local checks

Implemented under the approved manifest:

- Replaced the decoder's variable stroke array with a generation-only object requiring every bounded stroke key, then normalized it to the unchanged public content schema.
- Added distinct feature labels and safe duplicate geometry diagnostics, including first duplicate index and unique/duplicate counts.
- Tightened the prompt to request different subject parts and reduced generation from 12 paths to the contract minimum of 8 after call 2 showed eight unique paths before duplication.
- Kept duplicate geometry, source-copy, source-anchor, role, final-feature, first-step, stage, path-command and API validation gates enabled.

Final focused checks passed: Modal worker **30/30**, backend **12/12**, mobile **3/3**; Python compile and scoped `git diff --check` passed. These tests do not establish Qwen generation quality.

## Modal state and health

Three language/audio app revisions were deployed during this bounded cycle. Before each call, CPU `/health` reported the pinned Qwen checkpoint and catalog `ready`, with `gpu_allocated=false` and `inference_executed=false`. The health probes did not trigger inference. After call 3, the Modal app was stopped; `modal app info` confirmed `State: stopped` at 2026-11-15 12:20 SE Asia Standard Time. The catalog Volume was not mutated.

## Evidence index

- `attempt_001_*`, `attempt_002_summary.json`, `attempt_002_response.json`, and `attempt_003_*`: sanitized Parent runner outcomes.
- `modal_worker_attempt_001_logs.txt`, `modal_worker_attempt_002_logs.txt`, `modal_worker_attempt_003_final_logs.txt`: call-specific Modal logs and terminal diagnostics.
- `modal_worker_attempt_003_progress_logs.txt`: interim phase logs from the final call.
- `health*.json`, `modal_preflight.txt`, `modal_app_stopped.txt`: health and app lifecycle.
- `run_parent_construction_guide.py`: real route/worker harness; it bypasses only local identity/database authorization and uses the synthetic topic.

## Next technical direction

Free-form model-authored SVG `d` strings remain too fragile: the failure moved from repeated geometry to path-command complexity. A follow-up should have Qwen output a bounded semantic geometry representation (primitive type plus coordinates) and let deterministic code render the short SVG paths. The renderer should validate bounds, degeneracy, path count and uniqueness; the existing stage/source/final-feature gates remain. This is a new implementation cycle. No UI, Android/Firebase E2E, Teacher presentation, or child-readability evaluation is claimed here.

SRS §§1–31 are unchanged. SRS §32.35 records only this environment-specific result; the SRS remains unsigned.
