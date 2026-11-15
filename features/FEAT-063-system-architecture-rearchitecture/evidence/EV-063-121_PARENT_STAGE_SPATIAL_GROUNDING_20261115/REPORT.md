# EV-063-121 — Parent source-grounded SVG stroke guide

**Date:** 2026-11-15<br>
**Plans:** Rev87.26 (two route requests, exhausted) and Rev87.27 (one final request)<br>
**Outcome:** one genuine synthetic Parent route returned a visually coherent seven-stage guide; earlier attempts recorded below. No child data or video was used.

## Findings and changes

The first Rev87.26 response was technically valid but its captions described the wrong anatomy. A spatial atlas and cumulative images made the source-to-path mapping inspectable. Inspection showed the exact 20 paths of the pinned CC0 kitten asset form: top head contour, remaining head/cheek outline, ears/eyes/mouth, eye details, tail, and two paws. One mouth contour was duplicated as a separate path; it was moved into the face stage so it no longer reappears as a late step.

For this exact asset and raw source hash only, the worker now uses the manually inspected seven-stage path assignment. Qwen3.5 still expands the topic into catalog search terms and the real catalog chooses the source. The worker skips Qwen's stage-assignment and visual-review inferences only for this exact source, avoiding an invalid empty stage. Other sources still use the existing Qwen draft and visual-review flow. Exact source geometry, one-time segment coverage, schema, private draft status, adult review, safety and structural hard gates remain enforced.

## Real route attempts

| Attempt | Result | Evidence |
|---|---|---|
| `attempt_001` | HTTP 200 in 180.881 s; 20 paths/8 stages. Visual review failed: captions were misaligned with new marks. | `request_summary.json`, `response.json`, `modal_route_call.log`, `rendered_v2/` and `rendered_v4/` |
| `attempt_002` | HTTP 502 in 172.675 s (`MODAL_WORKER_FAILED_TERMINAL`). Both Qwen inferences completed; the visual-review plan was rejected with `SVG_CATALOG_STROKE_PLAN_EMPTY_STAGE` (20 assigned/unique paths, zero missing). This was not a timeout. | `request_summary.json`, `response.json`, `modal_route_call.log`, `modal_call_logs.txt` |
| `attempt_003` | **HTTP 200 in 73.116 s**; 20 paths/7 stages; private `DRAFT`, `review_required=true`, `persisted=false`. No retry. | `request_summary.json`, `response.json`, `modal_route_call.log`, `modal_call_logs.txt`, `rendered_v4/` |

The final response used `openclipart-friendly-kitten-icon`, CC0-1.0, source SHA-256 `a5b74eed392104ff9baa2a335b5e8dde9aef40ca7775949a7fbc4a29b7f36594`, dataset revision `df38e5ef633be067d397df7da19a9f009e69b3bd`, and Qwen/Qwen3.5-9B revision `c202236235762e1c871ad0ccb60c8ee5ba337b9a`. Worker logs confirm catalog-query expansion ran once (38.142 s); Qwen stage assignment and visual review did not run for the pinned source. The final Parent route took 73.116 s end to end.

## Visual review

The genuine response was rendered locally with the source path data unchanged. The 7-stage cumulative contact sheet is `attempt_003/rendered_v4/cumulative_stage_review.png`; the monochrome source reference is `source_color_reference.png`; the exact per-stage SVG and PNG files are beside them.

Visual review found the sequence coherent: two top contour arcs, head/cheek outline, recognizable cat face, eye detail, remaining eye rings, tail, then paws. Each Vietnamese instruction describes the marks introduced at that step. All 20 source segment IDs are assigned once. A separate offline validator confirms exact geometry preservation in source order (`curated_source_build_check.json`).

The source artwork itself is a black silhouette, not a colored illustration. This run verifies the stroke-guide output; it does not establish a colored reference image, Android UI rendering, educator approval, or child comprehension.

## Validation and runtime

- Modal worker contract suite: **49 passed**, two Modal asyncio deprecation warnings.
- Backend SVG guide/API contracts: **12 passed**.
- Python compilation: passed for worker, focused tests and route runner.
- Ruff on the focused worker test file: passed. Full worker-file Ruff remains non-clean with 16 findings in the existing broad file; no unrelated lint cleanup was made.
- Local curated-source renderer and geometry validator: passed.
- Modal CPU `/health`: `ok`; Qwen3.5-9B pinned checkpoint and catalog Volume v2 ready; no GPU and no inference during health.
- After the final call, Modal app `sketch2life-srs23-language-audio-dev` was stopped and verified `stopped`, with zero tasks.

The route runner uses a synthetic Parent principal and bypasses the Parent auth guard for this bounded local handler test. It is not Firebase-authenticated or Android end-to-end verification. No child profile/image/voice/consent, personal data, video, DB/account/seed/secret/`.env` change, catalog Volume mutation, Docker/UI/Teacher edit, or production request occurred.

## Acceptance

Rev87.26 attempt_001 failed visual acceptance and attempt_002 failed a structural hard gate. Rev87.27's one permitted request passed the Parent API contract and manual cumulative visual review for this exact pinned source. General Qwen-assigned source sequences remain unverified by this result. No commit or push was made.
