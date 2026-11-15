# EV-063-111 — Qwen Openclipart stroke assignment fix

**Date:** 2026-11-15 (Asia/Ho_Chi_Minh)<br>
**Plan:** [Rev87.16](../../plan/PLAN_REV87_16_MODAL_QWEN_CATALOG_PATH_ASSIGNMENT_FIX_20261115.md)<br>
**Result:** The corrected catalog-to-Qwen worker path passed one real synthetic request. This does not establish Parent API/UI/Android or Teacher presentation E2E.

## What failed before

EV-063-110 showed the Qwen worker reaching generation, then rejecting its stage arrays because they did not cover every selected source path exactly once. That run intentionally did not retain raw model text, so it cannot tell whether a path was omitted or duplicated. It was not a timeout.

The old schema constrained each stage's `path_ids` to known values, but JSON Schema/LMFE could not require the union of several arrays to equal the selected path set. The worker was asking Qwen to satisfy a cross-array set invariant that the schema could not express.

## Fix

- The internal plan is now `SvgOpenclipartSourceStrokePlanV2`. Qwen supplies 4–8 labelled stages and a `path_stage_assignments` object.
- The constrained schema makes every selected source path ID a required object key, forbids extra keys, and restricts stage values to 1–8. The parser separately verifies each value is within the actual stage count and rejects empty stages.
- Duplicate JSON object keys are rejected before ordinary JSON parsing could silently overwrite one. Safe diagnostics record only counts/reason codes; no prompt, raw model output, source SVG text, child data or credentials are logged.
- After validation, the worker builds each stage's path list in original source order. The renderer still copies the exact sanitized source path geometry; Qwen cannot create or replace geometry.

## Verification

| Check | Result |
|---|---|
| Focused worker contract tests | **16 passed, 2 skipped** |
| Skip reason | `lm-format-enforcer` is only installed in the pinned Modal image, not the local Python environment |
| Ruff on contract tests | **Pass** |
| Ruff `SIM102` on changed worker path | **Pass** |
| Python compile | **Pass** |
| Modal deployment | **Pass**, app deployed in 13.974 s |
| CPU `/health` | **Pass**, Qwen and Volume catalog ready; no GPU allocation/inference by health |
| Real Modal worker inference | **Pass**, one synthetic request, no retry |

The deployed worker exercised the pinned LMFE schema at runtime: constrained decoder setup completed, EOS was reached, and the parser accepted the generated assignment map.

## Real request result

- Topic: `con mèo`; difficulty: `beginner`.
- Model: `Qwen/Qwen3.5-9B`, revision `c202236235762e1c871ad0ccb60c8ee5ba337b9a`.
- Modal call: `fc-01M7DW7AGGFFQRV4QPG70ZVEH5`.
- End-to-end worker call duration: 86.088 s.
- Selected source: Openclipart `openclipart-friendly-kitten-icon`, CC0-1.0, [source page](https://openclipart.org/236739/friendly-kitten-icon), source SHA-256 `a5b74eed392104ff9baa2a335b5e8dde9aef40ca7775949a7fbc4a29b7f36594`.
- Dataset revision: `df38e5ef633be067d397df7da19a9f009e69b3bd`.
- Result: 11 source paths assigned exactly once across six stages; the same 11 path IDs and geometry appear in the line guide and color reference. All eight runner quality checks passed, including CC0 provenance and the 256 KiB output limit.
- Qwen's six short instructions progress through the cat outline, ears, eyes, nose, mouth and fur. Per-stage source path IDs are in [modal-worker-summary.json](modal-worker-summary.json); full validated output is in [modal-worker-output.json](modal-worker-output.json).
- No retry, child data, image, voice, account, DB/consent, video or fixture was used.

## Timings from Modal worker events

| Phase | Duration |
|---|---:|
| Model load | 17.656 s |
| Catalog query expansion | 38.612 s |
| Candidate search | 1.570 s |
| Source render | 0.293 s |
| Prompt encoding | 0.021 s |
| Constrained decoder setup | 0.001 s |
| Qwen inference | 17.743 s |
| Output validation | <0.001 s |
| Worker execution | 76.323 s |
| Runner elapsed | 86.088 s |

Full bounded logs: [modal-worker-logs.txt](modal-worker-logs.txt). The health payload is [modal-health.json](modal-health.json); machine-readable attempt details are in [runtime-attempt.json](runtime-attempt.json).

## Visual review artifact

[guide-preview.html](guide-preview.html) shows the six cumulative line stages and the matching color source. The standalone `stage-01.svg` through `stage-06.svg` and `color-reference.svg` were generated from the actual returned Modal output, not from fixtures.

## Limits and current state

- This verifies the deployed **catalog → Qwen worker → source-bound SVG result** path only. The authenticated Parent API, Parent UI, Android emulator and Teacher presentation were not exercised.
- The product workload flag remains disabled by default. The Qwen app is deployed in `dev`, with `min_containers=0` and a 120-second scale-down window; the health call itself kept no GPU warm.
- The full corpus remains on Modal Volume v2. No Docker/repository copy or Volume deletion occurred.
- No commit or push was made.
