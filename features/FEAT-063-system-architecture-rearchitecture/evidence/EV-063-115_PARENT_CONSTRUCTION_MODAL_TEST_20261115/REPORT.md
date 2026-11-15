# EV-063-115 — Parent construction-guide bounded verification

**Date:** 2026-11-15 (Asia/Saigon)<br>
**Plan:** Rev87.19, approved SHA-256 `569C07B61C6BA73D859C0ADE5AE402232AB3EFADB20F112659C03395DC2D8B3B`<br>
**Outcome:** PARTIAL — local contract work and tests passed; the only live model result was rejected; no guide image was produced.

## Scope used

The one live request used only the synthetic topic `con mèo`. No child profile, photo, voice, consent, real personal data, video, or database entity was supplied. The HTTP TestClient preflight failed before dispatch, so the one actual request invoked the Parent route handler directly with its identity/database dependency wrappers bypassed. This is not authenticated Parent API or Android end-to-end evidence.

## Runtime result

| Item | Result |
|---|---|
| Request ID | `13cdae7d-15b4-44cd-b47f-84fe983d0fd4` |
| Modal call | `fc-01M7E7RJSYRAPJ9HR0XD0NYSSG` |
| Model | `Qwen/Qwen3.5-9B`, revision `c202236235762e1c871ad0ccb60c8ee5ba337b9a` |
| Selected reference geometry | 11 source paths |
| Parent handler response | HTTP 502, `MODAL_WORKER_FAILED_TERMINAL` |
| Worker failure | `SVG_CONSTRUCTION_GUIDE_GEOMETRY_COMPLEXITY_INVALID` at `output_parse_and_source_identity_validation` |
| Model inference duration | 146.733 seconds |
| Catalog query expansion | 45.720 seconds |
| Total worker duration | 216.720 seconds |
| End-to-end handler duration | 234.273 seconds |
| SVG/API guide returned | No |
| SVG rendered or visually reviewed | No |
| Retry/additional inference | No |

This was a completed model inference followed by worker validation failure, not a 30-minute timeout or Modal GPU startup timeout. The worker emitted zero parsed strokes and zero stages. Its earlier combined complexity gate did not retain raw model output or identify whether aggregate geometry size or duplicate geometry caused rejection; the exact subreason is unrecoverable from the retained evidence. The API wait log initially missed the terminal worker event, while the detailed worker log contains the rejection and traceback.

The HTTP TestClient harness preflight returned 500 in 3.335 seconds and dispatched no worker. Read-only Modal logs for that period showed no worker invocation. See `http_harness_preflight.json`.

## Changes after the failed request

The local worker/backend contract now uses a 16,384-character aggregate geometry bound, matching the maximum permitted by the versioned 20-stroke/768-character-per-stroke schema. The prompt now asks for 8–20 construction strokes. Safe worker diagnostics distinguish duplicate geometry from aggregate-size rejection and include bounded counts. These are code-level corrections only; because the sole approved inference had already failed, the effect on live model output is unverified.

The updated language/audio Modal app was deployed to the `dev` environment after the local correction, without another inference, then stopped. A read-only app listing showed the app stopped. Lifecycle details are recorded in `modal_postfix_lifecycle.json`. No GPU worker was intentionally left running. The deployment does not prove that a later request returns a valid guide.

## Local verification

- Backend focused construction-guide/API/source-derived-guide tests: **12 passed**.
- Modal worker construction-guide contract tests: **25 passed**, 2 asyncio deprecation warnings.
- Parent mobile SVG guide contract/render tests: **3 passed**.
- These results cover local contracts and rendering behavior only. They do not replace the failed live output or establish child readability.

## Limits and follow-up

No second inference was run because Rev87.19 authorized at most one and forbids retry after a terminal failure. No Android UI, Teacher presentation, video, child data, or visual acceptance test occurred. The live generation and visual acceptance criteria in the plan remain unchecked. SRS §32.33 records this result as environment-specific as-built evidence; target §§1–31 are unchanged and the SRS remains unsigned.

## Evidence files

- `request.json`, `response.json`, and `request_summary.json`
- `http_harness_preflight.json`
- `modal_handler_call.log`
- `modal_worker_logs.txt`
- `modal_postfix_lifecycle.json`
- `test_results.txt`
